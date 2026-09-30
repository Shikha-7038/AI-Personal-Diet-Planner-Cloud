import random
import unittest

from ai_engine.ai_client import AIError, validate_ai_plan
from ai_engine.diet_engine import (calculate_targets, generate_rule_based_plan,
                                   normalise_avoid_list, MEAL_ORDER)


class TestTargets(unittest.TestCase):
    def test_calculate_targets_reasonable_ranges(self):
        t = calculate_targets({"sex": "female", "age": 22, "height": 165, "weight": 62,
                               "activity_level": "moderate", "goal": "weight_management"})
        self.assertTrue(1200 <= t["target_calories"] <= 2200)
        self.assertGreater(t["bmr"], 0)
        self.assertEqual(t["target_calories"], max(1200, t["target_calories"]))

    def test_calorie_floor_never_broken(self):
        t = calculate_targets({"sex": "female", "age": 60, "height": 150, "weight": 45,
                               "activity_level": "sedentary", "goal": "weight_management"})
        self.assertGreaterEqual(t["target_calories"], 1200)

    def test_goal_changes_calories(self):
        base = {"sex": "male", "age": 25, "height": 175, "weight": 70, "activity_level": "moderate"}
        cut = calculate_targets({**base, "goal": "weight_management"})["target_calories"]
        gain = calculate_targets({**base, "goal": "fitness"})["target_calories"]
        self.assertLess(cut, gain)


class TestRuleBasedPlan(unittest.TestCase):
    def profile(self, **overrides):
        base = {"sex": "female", "age": 22, "height": 165, "weight": 62, "activity_level": "moderate",
               "goal": "balanced", "dietary_preference": "general", "allergies": []}
        base.update(overrides)
        return base

    def test_plan_has_all_meals(self):
        plan = generate_rule_based_plan(self.profile(), rng=random.Random(1))
        for meal in MEAL_ORDER:
            self.assertIn(meal, plan)
            self.assertGreater(plan[meal]["kcal"], 0)
        self.assertIn("nutrition_summary", plan)
        self.assertIn("disclaimer", plan)
        self.assertEqual(plan["source"], "rule_based")

    def test_vegan_plan_excludes_animal_products(self):
        plan = generate_rule_based_plan(self.profile(dietary_preference="vegan"), rng=random.Random(2))
        blocked = ("egg", "chicken", "fish", "paneer", "curd", "yogurt")
        for meal in MEAL_ORDER:
            desc = plan[meal]["description"].lower()
            for word in blocked:
                self.assertNotIn(word, desc, f"{meal} should not contain '{word}' for a vegan profile")

    def test_allergy_word_is_excluded(self):
        plan = generate_rule_based_plan(self.profile(allergies=["nuts", "dairy"]), rng=random.Random(3))
        for meal in MEAL_ORDER:
            desc = plan[meal]["description"].lower()
            self.assertNotIn("almond", desc)
            self.assertNotIn("paneer", desc)

    def test_totals_match_sum_of_meals(self):
        plan = generate_rule_based_plan(self.profile(), rng=random.Random(4))
        summed = sum(plan[m]["kcal"] for m in MEAL_ORDER)
        self.assertEqual(summed, plan["nutrition_summary"]["total_calories"])

    def test_normalise_avoid_list_synonyms(self):
        tags, words = normalise_avoid_list(["Peanuts", "custom-food-xyz"])
        self.assertIn("nuts", tags)
        self.assertIn("custom-food-xyz", words)


class TestAIValidation(unittest.TestCase):
    def test_missing_meal_raises(self):
        with self.assertRaises(AIError):
            validate_ai_plan({"breakfast": {"description": "toast"}}, {"dietary_preference": "general"})

    def test_meat_rejected_for_vegetarian(self):
        raw = {m: {"description": "grilled chicken bowl"} for m in MEAL_ORDER}
        raw["nutrition_summary"] = "test"
        with self.assertRaises(AIError):
            validate_ai_plan(raw, {"dietary_preference": "vegetarian"})

    def test_valid_plan_passes(self):
        raw = {m: {"description": "vegetable soup", "approx_kcal": 300} for m in MEAL_ORDER}
        raw["nutrition_summary"] = "balanced demo plan"
        plan = validate_ai_plan(raw, {"dietary_preference": "vegan", "allergies": []})
        for m in MEAL_ORDER:
            self.assertIn(m, plan)


if __name__ == "__main__":
    unittest.main()
