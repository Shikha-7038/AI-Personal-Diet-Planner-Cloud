"""
Rule-based diet recommendation engine (VERSION A).

This module needs NO internet and NO paid API. It:
  1. Calculates calorie / macro targets (Mifflin-St Jeor BMR -> TDEE -> goal adjustment).
  2. Filters a small demo food dataset by diet type and allergies/foods to avoid.
  3. Picks a main dish + portion size (+ optional side) for each meal so that the
     totals get close to the calorie/protein targets.

EDUCATIONAL DEMO ONLY - not medical or clinical nutrition advice.
"""
import json
import random
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).with_name("food_data.json")

DISCLAIMER = (
    "Educational / general wellness example generated from a small demo dataset. "
    "It is NOT medical or clinical nutrition advice. Consult a qualified professional "
    "before changing your diet."
)
HYDRATION_REMINDER = (
    "General reminder: sip water regularly through the day (a common rule of thumb is "
    "roughly 2 litres, but needs vary with climate, activity and body size)."
)

# Physical Activity Level multipliers for TDEE
ACTIVITY_FACTORS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725}

# goal -> (calorie adjustment, protein %, carbs %, fat %)
GOAL_SETTINGS = {
    "balanced": (0.00, 0.20, 0.50, 0.30),
    "weight_management": (-0.15, 0.30, 0.40, 0.30),
    "fitness": (0.05, 0.30, 0.45, 0.25),
}
# how strongly we care about hitting the protein share for each goal
PROTEIN_WEIGHT = {"balanced": 0.2, "weight_management": 0.4, "fitness": 0.6}

# share of daily calories per meal
MEAL_SHARE = {"breakfast": 0.25, "lunch": 0.35, "snack": 0.10, "dinner": 0.30}
MEAL_ORDER = ["breakfast", "lunch", "snack", "dinner"]
PORTIONS = [0.75, 1.0, 1.25, 1.5]

# words a user may type -> canonical allergen tag used in food_data.json
ALLERGEN_SYNONYMS = {
    "nut": "nuts", "nuts": "nuts", "peanut": "nuts", "peanuts": "nuts", "almond": "nuts",
    "milk": "dairy", "dairy": "dairy", "lactose": "dairy", "curd": "dairy", "paneer": "dairy",
    "gluten": "gluten", "wheat": "gluten",
    "egg": "egg", "eggs": "egg",
    "soy": "soy", "soya": "soy", "tofu": "soy",
    "fish": "fish", "seafood": "fish",
}


def load_food_data() -> dict:
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def calculate_targets(profile: dict) -> dict:
    """Compute BMR, TDEE and daily calorie/macro targets from profile fields.

    Expected keys: sex, age, height (cm), weight (kg), activity_level, goal.
    """
    sex = profile.get("sex", "female")
    bmr = 10 * profile["weight"] + 6.25 * profile["height"] - 5 * profile["age"] + (5 if sex == "male" else -161)
    tdee = bmr * ACTIVITY_FACTORS.get(profile.get("activity_level"), 1.2)
    goal = profile.get("goal", "balanced")
    adjust, p_pct, c_pct, f_pct = GOAL_SETTINGS.get(goal, GOAL_SETTINGS["balanced"])
    calories = max(1200, round(tdee * (1 + adjust)))  # safety floor for a demo app
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "target_calories": calories,
        "target_macros_g": {
            "protein": round(calories * p_pct / 4),
            "carbs": round(calories * c_pct / 4),
            "fat": round(calories * f_pct / 9),
        },
    }


def normalise_avoid_list(allergies) -> tuple:
    """Split user-entered allergies into (allergen_tags, free_text_words)."""
    tags, words = set(), set()
    for raw in allergies or []:
        token = str(raw).strip().lower()
        if not token:
            continue
        if token in ALLERGEN_SYNONYMS:
            tags.add(ALLERGEN_SYNONYMS[token])
        else:
            words.add(token)
    return tags, words


def _diet_allows(user_diet: str, food_diet: str) -> bool:
    rank = {"vegan": 0, "vegetarian": 1, "general": 2}
    return rank.get(food_diet, 2) <= rank.get(user_diet, 2)


def _is_safe(food: dict, diet: str, tags: set, words: set) -> bool:
    if not _diet_allows(diet, food["diet"]):
        return False
    if tags.intersection(food.get("allergens", [])):
        return False
    name = food["name"].lower()
    return not any(w in name for w in words)


def _scale(food: dict, servings: float) -> dict:
    return {
        "name": food["name"],
        "servings": servings,
        "kcal": round(food["kcal"] * servings),
        "protein_g": round(food["p"] * servings, 1),
        "carbs_g": round(food["c"] * servings, 1),
        "fat_g": round(food["f"] * servings, 1),
    }


def _sum_items(items: list) -> dict:
    return {
        "kcal": round(sum(i["kcal"] for i in items)),
        "protein_g": round(sum(i["protein_g"] for i in items), 1),
        "carbs_g": round(sum(i["carbs_g"] for i in items), 1),
        "fat_g": round(sum(i["fat_g"] for i in items), 1),
    }


def _describe(items: list) -> str:
    parts = []
    for i in items:
        parts.append(i["name"] if i["servings"] == 1 else f"{i['name']} ({i['servings']:g}x portion)")
    return " + ".join(parts)


def _build_meal(meal: str, target_kcal: float, target_protein: float, goal: str,
                foods: list, sides: list, rng: random.Random) -> dict:
    """Score every (main, portion, optional side) combination and pick one of the best 3."""
    weight = PROTEIN_WEIGHT.get(goal, 0.2)
    scored = []
    for main in foods:
        for portion in PORTIONS:
            base = [_scale(main, portion)]
            options = [base] + [base + [_scale(s, 1)] for s in sides]
            for combo in options:
                tot = _sum_items(combo)
                score = abs(tot["kcal"] - target_kcal) / target_kcal
                score += weight * max(0.0, target_protein - tot["protein_g"]) / max(target_protein, 1)
                score += 0.03 * abs(portion - 1)  # prefer normal portions
                scored.append((score, combo))
    scored.sort(key=lambda x: x[0])
    _, best = rng.choice(scored[:3]) if len(scored) >= 3 else scored[0]
    totals = _sum_items(best)
    return {"description": _describe(best), "items": best, **totals}


def generate_rule_based_plan(profile: dict, targets: Optional[dict] = None,
                             rng: Optional[random.Random] = None) -> dict:
    """Generate a full-day plan (breakfast, lunch, snack, dinner) from a profile dict."""
    rng = rng or random.Random()
    targets = targets or calculate_targets(profile)
    data = load_food_data()
    diet = profile.get("dietary_preference", "general")
    goal = profile.get("goal", "balanced")
    tags, words = normalise_avoid_list(profile.get("allergies"))
    protein_target = targets["target_macros_g"]["protein"]

    plan = {}
    for meal in MEAL_ORDER:
        foods = [f for f in data["meals"][meal] if _is_safe(f, diet, tags, words)]
        sides = [s for s in data["sides"] if meal in s["meals"] and _is_safe(s, diet, tags, words)]
        if not foods:
            plan[meal] = {"description": "No matching option in the demo dataset for your preferences.",
                          "items": [], "kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
            continue
        share = MEAL_SHARE[meal]
        plan[meal] = _build_meal(meal, targets["target_calories"] * share,
                                 protein_target * share, goal, foods, sides, rng)

    totals = {
        "total_calories": sum(plan[m]["kcal"] for m in MEAL_ORDER),
        "protein_g": round(sum(plan[m]["protein_g"] for m in MEAL_ORDER), 1),
        "carbs_g": round(sum(plan[m]["carbs_g"] for m in MEAL_ORDER), 1),
        "fat_g": round(sum(plan[m]["fat_g"] for m in MEAL_ORDER), 1),
    }
    plan["nutrition_summary"] = {
        **targets, **totals,
        "note": "Approximate values from a small demo dataset; real foods vary.",
    }
    plan["hydration_reminder"] = HYDRATION_REMINDER
    plan["disclaimer"] = DISCLAIMER
    plan["source"] = "rule_based"
    plan["fallback_reason"] = None
    return plan
