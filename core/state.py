"""Shared session helpers and the daily-context builder used across views."""
from __future__ import annotations

import streamlit as st

from core import database as db
from core import gamification as g


def go(page: str) -> None:
    """Navigate to a page on the next rerun."""
    st.session_state.page = page
    st.rerun()


def ramadan_on() -> bool:
    return bool(db.get_meta("ramadan_mode", False))


def meals() -> list[tuple[str, str]]:
    """Meal sections + emojis — Ramadan mode swaps to Sehri/Iftar (#11)."""
    if ramadan_on():
        return [("Sehri", "🌙"), ("Iftar", "🌆"), ("Dinner", "🍽️"), ("Snacks", "🍪")]
    return [("Breakfast", "🌅"), ("Lunch", "🌞"), ("Dinner", "🌙"), ("Snacks", "🍪")]


def daily_context() -> dict:
    """One dict with everything the dashboard, coach and achievements need."""
    p = db.get_profile() or {}
    totals = db.day_totals()
    water = db.water_today()
    streak = g.current_streak()
    return {
        "profile": p,
        "goal": p.get("goal", "Maintain"),
        "calorie_goal": p.get("calorie_goal", 2000),
        "protein_goal": p.get("protein_g", 120),
        "carbs_goal": p.get("carbs_g", 200),
        "fat_goal": p.get("fat_g", 65),
        "water_goal": p.get("water_goal_ml", 2500),
        "consumed": totals["calories"],
        "remaining": p.get("calorie_goal", 2000) - totals["calories"],
        "protein": totals["protein"], "carbs": totals["carbs"],
        "fat": totals["fat"], "fiber": totals["fiber"], "items": totals["items"],
        "water": water,
        "streak": streak,
        "weight": p.get("weight_kg"),
        "target_weight": p.get("target_weight_kg"),
        "scanned": st.session_state.get("has_scanned", False),
    }


def run_achievement_check() -> None:
    """Evaluate achievements and queue celebrations for newly unlocked ones."""
    ctx = daily_context()
    newly = g.check_achievements(ctx)
    if newly:
        st.session_state.setdefault("pending_celebrations", []).extend(newly)
