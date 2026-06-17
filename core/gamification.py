"""
Gamification: streaks, achievements, levels/XP and consistency scoring.

Achievements are evaluated against live data and unlocked idempotently in the DB.
check_achievements() returns the list of *newly* unlocked ones so the UI can
fire a celebration.
"""
from __future__ import annotations

from datetime import date, timedelta

from core import database as db

# code -> (icon, name, description)
ACHIEVEMENTS = {
    "first_bite":   ("🍴", "First Bite", "Log your first food"),
    "ai_vision":    ("📸", "AI Vision", "Scan a meal with the camera"),
    "scale_step":   ("⚖️", "On the Scale", "Log your weight"),
    "hydrated":     ("💧", "Hydrated", "Hit your daily water goal"),
    "on_target":    ("🎯", "On Target", "Land within 100 kcal of your goal"),
    "protein_pro":  ("💪", "Protein Pro", "Reach your daily protein goal"),
    "streak_3":     ("🔥", "Warming Up", "3-day logging streak"),
    "streak_7":     ("🚀", "Week Warrior", "7-day logging streak"),
    "streak_30":    ("👑", "Unstoppable", "30-day logging streak"),
    "balanced":     ("🥗", "Balanced Day", "Hit all 3 macro goals in a day"),
    "explorer":     ("🧭", "Explorer", "Log 20 different foods"),
    "centurion":    ("🏆", "Centurion", "Log 100 foods total"),
}

LEVELS = [
    (0, "Sprout 🌱"), (150, "Rookie 🥚"), (400, "Tracker 🍃"),
    (800, "Achiever 🌟"), (1500, "Pro 💎"), (2600, "Elite 🔥"),
    (4200, "Legend 👑"),
]


def current_streak() -> int:
    """Consecutive days (ending today or yesterday) with at least one food log."""
    days = db.logged_dates()
    if not days:
        return 0
    streak, cursor = 0, date.today()
    if cursor.isoformat() not in days:
        cursor -= timedelta(days=1)          # allow streak to count through yesterday
        if cursor.isoformat() not in days:
            return 0
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak() -> int:
    days = sorted(db.logged_dates())
    if not days:
        return 0
    best = run = 1
    for i in range(1, len(days)):
        prev = date.fromisoformat(days[i - 1])
        cur = date.fromisoformat(days[i])
        if (cur - prev).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best


def consistency_score(days: int = 14) -> int:
    """% of the last `days` days that have at least one log."""
    logged = db.logged_dates()
    hit = sum(
        1 for i in range(days)
        if (date.today() - timedelta(days=i)).isoformat() in logged
    )
    return round(hit / days * 100)


def total_xp() -> int:
    """XP from logging activity + unlocked achievements."""
    foods = sum(1 for _ in db.export_all()["food_log"])
    weights = len(db.get_weights())
    ach = len(db.unlocked_codes())
    return foods * 12 + weights * 8 + ach * 50


def level_for(xp: int):
    name, idx = LEVELS[0][1], 0
    for i, (threshold, lname) in enumerate(LEVELS):
        if xp >= threshold:
            name, idx = lname, i
    cur_floor = LEVELS[idx][0]
    nxt = LEVELS[idx + 1][0] if idx + 1 < len(LEVELS) else cur_floor
    span = max(1, nxt - cur_floor)
    pct = 100 if idx + 1 >= len(LEVELS) else round((xp - cur_floor) / span * 100)
    return {"level": idx + 1, "name": name, "xp": xp,
            "next_at": nxt, "progress": min(100, pct),
            "is_max": idx + 1 >= len(LEVELS)}


def check_achievements(ctx: dict) -> list[dict]:
    """Evaluate all achievements; unlock & return any newly earned."""
    earned: list[str] = []
    totals = db.day_totals()
    distinct_foods = {f["name"] for f in db.export_all()["food_log"]}
    total_foods = len(db.export_all()["food_log"])
    streak = ctx.get("streak", current_streak())

    rules = {
        "first_bite":  totals["items"] >= 1 or total_foods >= 1,
        "ai_vision":   ctx.get("scanned"),
        "scale_step":  len(db.get_weights()) >= 1,
        "hydrated":    ctx.get("water", 0) >= ctx.get("water_goal", 10 ** 9),
        "on_target":   abs(totals["calories"] - ctx.get("calorie_goal", 0)) <= 100 and totals["items"] > 0,
        "protein_pro": totals["protein"] >= ctx.get("protein_goal", 10 ** 9) and totals["items"] > 0,
        "streak_3":    streak >= 3,
        "streak_7":    streak >= 7,
        "streak_30":   streak >= 30,
        "balanced":    (totals["protein"] >= ctx.get("protein_goal", 10 ** 9)
                        and totals["carbs"] >= ctx.get("carbs_goal", 10 ** 9)
                        and totals["fat"] >= ctx.get("fat_goal", 10 ** 9)),
        "explorer":    len(distinct_foods) >= 20,
        "centurion":   total_foods >= 100,
    }
    for code, ok in rules.items():
        if ok and db.unlock(code):
            earned.append(code)
    return [{"code": c, "icon": ACHIEVEMENTS[c][0], "name": ACHIEVEMENTS[c][1],
             "desc": ACHIEVEMENTS[c][2]} for c in earned]


def all_with_status() -> list[dict]:
    unlocked = db.unlocked_codes()
    return [{"code": c, "icon": i, "name": n, "desc": d, "unlocked": c in unlocked}
            for c, (i, n, d) in ACHIEVEMENTS.items()]
