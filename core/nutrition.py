"""
Nutrition science: BMR/TDEE, calorie & macro targets, and a built-in food database.

Calorie targets use the Mifflin–St Jeor equation (the modern clinical standard),
an activity multiplier for TDEE, and a goal-based deficit/surplus.
"""
from __future__ import annotations

ACTIVITY = {
    "Sedentary":        (1.20, "Little or no exercise"),
    "Lightly active":   (1.375, "Light exercise 1–3 days/wk"),
    "Moderately active": (1.55, "Moderate exercise 3–5 days/wk"),
    "Very active":      (1.725, "Hard exercise 6–7 days/wk"),
    "Athlete":          (1.90, "Training twice a day"),
}

GOALS = {
    "Lose weight":   {"emoji": "📉", "delta_per_kg": -1100, "macro": (0.35, 0.35, 0.30)},
    "Maintain":      {"emoji": "⚖️", "delta_per_kg": 0,     "macro": (0.30, 0.40, 0.30)},
    "Gain weight":   {"emoji": "📈", "delta_per_kg": +1100, "macro": (0.25, 0.45, 0.30)},
    "Build muscle":  {"emoji": "💪", "delta_per_kg": +700,  "macro": (0.35, 0.40, 0.25)},
}
# delta_per_kg: kcal/day adjustment per kg/week of target rate (~7700 kcal / 7 days ≈ 1100)


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "Male" else -161)


def tdee(sex: str, weight_kg: float, height_cm: float, age: int, activity: str) -> float:
    mult = ACTIVITY.get(activity, (1.2, ""))[0]
    return bmr(sex, weight_kg, height_cm, age) * mult


def calorie_target(sex, weight_kg, height_cm, age, activity, goal, rate_kg_wk=0.5) -> int:
    maint = tdee(sex, weight_kg, height_cm, age, activity)
    g = GOALS.get(goal, GOALS["Maintain"])
    # delta_per_kg is kcal/day for a 1 kg/week rate; scale by the chosen rate.
    target = maint + (g["delta_per_kg"] * rate_kg_wk)
    floor = 1200 if sex == "Female" else 1500
    return int(max(floor, round(target / 10) * 10))


def macro_targets(calories: int, goal: str) -> dict:
    p_ratio, c_ratio, f_ratio = GOALS.get(goal, GOALS["Maintain"])["macro"]
    return {
        "protein_g": round(calories * p_ratio / 4),
        "carbs_g":   round(calories * c_ratio / 4),
        "fat_g":     round(calories * f_ratio / 9),
    }


def water_goal(weight_kg: float) -> int:
    """~35 ml per kg of body weight, rounded to nearest 250 ml."""
    ml = weight_kg * 35
    return int(round(ml / 250) * 250)


def build_targets(p: dict) -> dict:
    """Given a profile dict, compute all daily targets."""
    cals = calorie_target(p["sex"], p["weight_kg"], p["height_cm"], p["age"],
                          p["activity"], p["goal"], p.get("rate_kg_wk", 0.5))
    macros = macro_targets(cals, p["goal"])
    return {
        "calorie_goal": cals,
        "protein_g": macros["protein_g"],
        "carbs_g": macros["carbs_g"],
        "fat_g": macros["fat_g"],
        "water_goal_ml": water_goal(p["weight_kg"]),
    }


def predict_goal_date(current_kg: float, target_kg: float, rate_kg_wk: float):
    """Return (weeks, calendar_date) to reach target at the chosen rate, or None."""
    from datetime import date, timedelta
    if current_kg is None or target_kg is None or not rate_kg_wk or rate_kg_wk <= 0:
        return None
    if abs(current_kg - target_kg) < 0.1:
        return None
    weeks = abs(current_kg - target_kg) / rate_kg_wk
    return round(weeks, 1), (date.today() + timedelta(weeks=weeks))


# --------------------------- Built-in food database --------------------------
# Per single serving (the "unit" describes that serving). Used for manual add,
# search, and as the knowledge base for the AI fallback recognizer.
FOODS = [
    # name, emoji, unit, kcal, protein, carbs, fat, fiber
    ("Oatmeal", "🥣", "1 bowl", 220, 8, 40, 4, 6),
    ("Greek Yogurt", "🥛", "170 g", 130, 17, 9, 0, 0),
    ("Banana", "🍌", "1 medium", 105, 1, 27, 0, 3),
    ("Apple", "🍎", "1 medium", 95, 0, 25, 0, 4),
    ("Scrambled Eggs", "🍳", "2 eggs", 180, 12, 2, 14, 0),
    ("Avocado Toast", "🥑", "1 slice", 290, 8, 30, 16, 7),
    ("Grilled Chicken Breast", "🍗", "150 g", 250, 46, 0, 6, 0),
    ("Salmon Fillet", "🐟", "150 g", 280, 39, 0, 13, 0),
    ("Brown Rice", "🍚", "1 cup", 215, 5, 45, 2, 4),
    ("Quinoa", "🌾", "1 cup", 222, 8, 39, 4, 5),
    ("Caesar Salad", "🥗", "1 bowl", 360, 10, 12, 30, 4),
    ("Mixed Green Salad", "🥬", "1 bowl", 150, 4, 14, 9, 5),
    ("Spaghetti Bolognese", "🍝", "1 plate", 540, 25, 70, 18, 6),
    ("Margherita Pizza", "🍕", "2 slices", 520, 22, 64, 20, 4),
    ("Cheeseburger", "🍔", "1 burger", 550, 28, 42, 30, 3),
    ("Sushi Roll", "🍣", "8 pieces", 320, 12, 56, 6, 3),
    ("Caesar Wrap", "🌯", "1 wrap", 430, 24, 38, 21, 4),
    ("Chicken Stir-fry", "🥘", "1 plate", 410, 32, 30, 18, 6),
    ("Beef Steak", "🥩", "200 g", 460, 50, 0, 28, 0),
    ("Tofu Bowl", "🍲", "1 bowl", 350, 20, 35, 14, 7),
    ("Protein Shake", "🥤", "1 scoop", 160, 27, 6, 3, 1),
    ("Almonds", "🥜", "30 g", 170, 6, 6, 15, 3),
    ("Peanut Butter", "🥜", "2 tbsp", 190, 8, 6, 16, 2),
    ("Dark Chocolate", "🍫", "30 g", 170, 2, 13, 12, 3),
    ("Strawberries", "🍓", "1 cup", 50, 1, 12, 0, 3),
    ("Blueberries", "🫐", "1 cup", 85, 1, 21, 0, 4),
    ("Orange", "🍊", "1 medium", 62, 1, 15, 0, 3),
    ("Coffee (black)", "☕", "1 cup", 5, 0, 0, 0, 0),
    ("Latte", "☕", "1 cup", 120, 6, 10, 6, 0),
    ("Croissant", "🥐", "1 piece", 270, 5, 31, 14, 1),
    ("Pancakes", "🥞", "3 cakes", 350, 8, 58, 10, 2),
    ("French Fries", "🍟", "medium", 365, 4, 48, 17, 4),
    ("Ice Cream", "🍦", "1 scoop", 210, 4, 24, 11, 0),
    ("Hummus", "🥙", "100 g", 170, 5, 14, 10, 4),
    ("Lentil Soup", "🍲", "1 bowl", 230, 15, 36, 3, 9),
    ("Cottage Cheese", "🧀", "150 g", 120, 14, 5, 5, 0),
    ("Whole Wheat Bread", "🍞", "1 slice", 80, 4, 14, 1, 2),
    ("Boiled Egg", "🥚", "1 egg", 78, 6, 1, 5, 0),
    ("Mango", "🥭", "1 cup", 100, 1, 25, 0, 3),
    ("Sweet Potato", "🍠", "1 medium", 115, 2, 27, 0, 4),
]

FOOD_KEYS = ("name", "emoji", "unit", "calories", "protein", "carbs", "fat", "fiber")


def food_dict(t) -> dict:
    return dict(zip(FOOD_KEYS, t))


def all_foods() -> list[dict]:
    """Built-in everyday foods + BD/fruit/fast-food catalog + extras + user custom foods."""
    from core import foods_bd
    try:
        from core.foods_img import EVERYDAY_IMAGES
    except Exception:
        EVERYDAY_IMAGES = {}
    builtins = [{**food_dict(t), "cat": "Everyday",
                 "image": EVERYDAY_IMAGES.get(t[0], "")} for t in FOODS]
    out = builtins + [dict(f) for f in foods_bd.FOODS_BD]
    try:
        from core import foods_bd_extra
        out += [dict(f) for f in foods_bd_extra.FOODS_BD_EXTRA]
    except Exception:
        pass
    try:
        from core import foods_extra
        out += [dict(f) for f in foods_extra.FOODS_EXTRA]
    except Exception:
        pass
    try:
        from core import database as db
        out += [{**c, "cat": "My Foods"} for c in db.get_custom_foods()]
    except Exception:
        pass
    return out


# Display order for the cuisine filter
CATEGORY_ORDER = ["All", "My Foods", "Bangladeshi", "Fruit", "Drinks",
                  "Sweets", "Fast food", "Everyday"]


def categories() -> list[str]:
    present = {f.get("cat", "Everyday") for f in all_foods()}
    ordered = [c for c in CATEGORY_ORDER if c == "All" or c in present]
    # append any categories not in the predefined order (future-proof)
    ordered += [c for c in sorted(present) if c not in ordered]
    return ordered


def search_foods(query: str, limit: int = 14, category: str = "All") -> list[dict]:
    q = (query or "").strip().lower()
    items = all_foods()
    if category and category != "All":
        items = [f for f in items if f.get("cat") == category]
    if not q:
        return items[:limit]
    scored = []
    for f in items:
        name = f["name"].lower()
        if name.startswith(q):
            scored.append((0, f))
        elif q in name:
            scored.append((1, f))
    scored.sort(key=lambda x: x[0])
    return [f for _, f in scored][:limit]


def find_food(name: str) -> dict | None:
    for f in all_foods():
        if f["name"].lower() == name.lower():
            return f
    return None
