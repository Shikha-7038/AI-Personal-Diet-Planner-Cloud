"""
Optional AI API client (VERSION B).

Sends structured (non-identifying) preferences to an AI service and validates the reply.
Two providers are supported so students can use whatever free/trial key they have:
  * "anthropic"          -> Anthropic Messages API
  * "openai_compatible"  -> any OpenAI-style /chat/completions endpoint
                            (set AI_BASE_URL, e.g. a free-tier provider)
If anything goes wrong we raise AIError and the planner falls back to the rule engine.
The API key is read from environment variables by the caller - never hardcode it.
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

from ai_engine.diet_engine import DISCLAIMER, HYDRATION_REMINDER, MEAL_ORDER

logger = logging.getLogger("diet_planner.ai")


class AIError(Exception):
    """Raised when the AI service is unavailable or returns an unusable answer."""


@dataclass(frozen=True)
class AISettings:
    provider: str = "none"          # none | anthropic | openai_compatible
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    timeout: float = 20.0

    @property
    def enabled(self) -> bool:
        return self.provider in ("anthropic", "openai_compatible") and bool(self.api_key)


SYSTEM_PROMPT = (
    "You are a general wellness meal-idea assistant for an educational demo app. "
    "You do NOT give medical advice. Reply with ONLY a JSON object, no markdown, in this exact shape: "
    '{"breakfast": {"description": str, "approx_kcal": int}, "lunch": {...}, "snack": {...}, '
    '"dinner": {...}, "nutrition_summary": str}. '
    "Respect the diet type and allergies strictly."
)

# keyword lists used to sanity-check the AI answer against the user's diet
MEAT_WORDS = ["chicken", "mutton", "lamb", "beef", "pork", "fish", "prawn", "shrimp", "tuna", "salmon", "meat", "bacon"]
NON_VEGAN_WORDS = ["egg", "milk", "paneer", "curd", "yogurt", "yoghurt", "cheese", "ghee", "butter", "honey", "whey"]


def build_prompt(profile: dict, targets: dict) -> str:
    """Prompt construction: only diet-relevant fields are sent (no name/email)."""
    payload = {
        "diet_type": profile.get("dietary_preference"),
        "goal": profile.get("goal"),
        "activity_level": profile.get("activity_level"),
        "allergies_or_foods_to_avoid": profile.get("allergies") or [],
        "extra_preferences": profile.get("preferences") or "",
        "daily_calorie_target": targets["target_calories"],
        "daily_macro_targets_g": targets["target_macros_g"],
    }
    return "Create a one-day meal plan for this demo user:\n" + json.dumps(payload)


def _call_provider(settings: AISettings, prompt: str) -> str:
    try:
        if settings.provider == "anthropic":
            url = (settings.base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages"
            resp = requests.post(
                url,
                headers={"x-api-key": settings.api_key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": settings.model or "claude-haiku-4-5-20251001", "max_tokens": 900,
                      "system": SYSTEM_PROMPT, "messages": [{"role": "user", "content": prompt}]},
                timeout=settings.timeout,
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        url = settings.base_url.rstrip("/") + "/chat/completions"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {settings.api_key}", "content-type": "application/json"},
            json={"model": settings.model, "temperature": 0.7,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": prompt}]},
            timeout=settings.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.RequestException as exc:
        raise AIError(f"AI request failed: {exc.__class__.__name__}") from exc
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise AIError("AI response had an unexpected structure") from exc


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise AIError("AI response did not contain JSON")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise AIError("AI response JSON was malformed") from exc


def validate_ai_plan(raw: dict, profile: dict) -> dict:
    """Response validation: shape, non-empty meals, diet rules and allergy words."""
    diet = profile.get("dietary_preference", "general")
    avoid = [str(a).lower() for a in (profile.get("allergies") or []) if str(a).strip()]
    plan, kcal_values = {}, []
    for meal in MEAL_ORDER:
        item = raw.get(meal)
        if isinstance(item, str):
            item = {"description": item}
        if not isinstance(item, dict) or not str(item.get("description", "")).strip():
            raise AIError(f"AI plan is missing '{meal}'")
        desc = str(item["description"]).strip()[:300]
        low = desc.lower()
        if diet in ("vegetarian", "vegan") and any(w in low for w in MEAT_WORDS):
            raise AIError(f"AI '{meal}' contains non-vegetarian food")
        if diet == "vegan" and any(w in low for w in NON_VEGAN_WORDS):
            raise AIError(f"AI '{meal}' contains non-vegan food")
        if any(a in low for a in avoid):
            raise AIError(f"AI '{meal}' mentions a food the user avoids")
        kcal = item.get("approx_kcal")
        kcal = int(kcal) if isinstance(kcal, (int, float)) and 0 < kcal < 2000 else None
        kcal_values.append(kcal)
        plan[meal] = {"description": desc, "items": [], "kcal": kcal}
    summary_text = str(raw.get("nutrition_summary", "")).strip()[:500]
    if not summary_text:
        raise AIError("AI plan is missing nutrition_summary")
    plan["_summary_text"] = summary_text
    plan["_total"] = sum(kcal_values) if all(k is not None for k in kcal_values) else None
    return plan


def generate_ai_plan(profile: dict, targets: dict, settings: AISettings) -> dict:
    """Call the AI provider and return a plan in the same shape as the rule-based engine."""
    if not settings.enabled:
        raise AIError("AI provider not configured")
    text = _call_provider(settings, build_prompt(profile, targets))
    plan = validate_ai_plan(_extract_json(text), profile)
    summary_text, total = plan.pop("_summary_text"), plan.pop("_total")
    plan["nutrition_summary"] = {**targets, "total_calories": total, "ai_notes": summary_text,
                                 "note": "Approximate values estimated by an AI model."}
    plan["hydration_reminder"] = HYDRATION_REMINDER
    plan["disclaimer"] = DISCLAIMER
    plan["source"] = "ai"
    plan["fallback_reason"] = None
    return plan
