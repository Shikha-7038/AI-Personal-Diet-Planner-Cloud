"""Planner: try the AI API first, fall back to the local rule-based engine on ANY AI failure."""
import logging
import random
from typing import Optional

from ai_engine.ai_client import AIError, AISettings, generate_ai_plan
from ai_engine.diet_engine import calculate_targets, generate_rule_based_plan

logger = logging.getLogger("diet_planner.planner")


def create_plan(profile: dict, ai_settings: Optional[AISettings] = None,
                rng: Optional[random.Random] = None) -> dict:
    """Return a diet plan dict. `plan["source"]` tells which engine produced it."""
    targets = calculate_targets(profile)
    reason = None
    if ai_settings is not None and ai_settings.enabled:
        try:
            return generate_ai_plan(profile, targets, ai_settings)
        except AIError as exc:
            reason = str(exc)
            logger.warning("AI plan failed (%s) - using rule-based fallback", reason)
    plan = generate_rule_based_plan(profile, targets, rng)
    plan["fallback_reason"] = reason
    return plan
