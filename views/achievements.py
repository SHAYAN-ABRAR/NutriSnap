"""Achievements, level, streaks and consistency — the gamification hub."""
from __future__ import annotations

import streamlit as st

from core import components as C
from core import gamification as gm
from core import i18n
from core.i18n import t


def render(p: dict) -> None:
    C.section("Achievements", "Build the habit, earn the badges.", "🏆")

    xp = gm.total_xp()
    lvl = gm.level_for(xp)
    streak = gm.current_streak()
    best = gm.longest_streak()

    # ---- level card ----
    with C.card():
        days_lbl = i18n.tf(f"{streak} days", f"{streak} দিন")
        level_lbl = i18n.tf(f"LEVEL {lvl['level']}", f"লেভেল {lvl['level']}")
        C.html(
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<div><div class='ns-sub'>{level_lbl}</div>"
            f"<div class='ns-h' style='font-size:1.4rem'>{t(lvl['name'])}</div></div>"
            f"<div class='ns-pill accent'><span class='flame'>🔥</span> {days_lbl}</div></div>"
        )
        nxt = i18n.tf(f"{lvl['next_at'] - xp} XP to level {lvl['level']+1}",
                      f"লেভেল {lvl['level']+1}-এ {lvl['next_at'] - xp} XP বাকি")
        st.progress(lvl["progress"] / 100, text=t("Max level reached 🎉") if lvl["is_max"] else nxt)

    C.metric_grid([
        (t("Total XP"), f"{xp}", "var(--accent)"),
        (t("Current streak"), f"{streak} 🔥", "var(--carbs)"),
        (t("Best streak"), f"{best} 🔥", "var(--protein)"),
        (t("Consistency"), f"{gm.consistency_score()}%", "var(--fiber)"),
    ])

    # ---- badge grid ----
    badges = gm.all_with_status()
    unlocked = [b for b in badges if b["unlocked"]]
    C.section(i18n.tf(f"Badges · {len(unlocked)}/{len(badges)}",
                      f"ব্যাজ · {len(unlocked)}/{len(badges)}"))

    rows = [badges[i:i + 3] for i in range(0, len(badges), 3)]
    for row in rows:
        cols = st.columns(3)
        for col, b in zip(cols, row):
            cls = "ns-badge" if b["unlocked"] else "ns-badge locked"
            check = "✓" if b["unlocked"] else "🔒"
            col.markdown(
                f"<div class='{cls}'><div class='ic'>{b['icon']}</div>"
                f"<div class='nm'>{t(b['name'])} {check}</div>"
                f"<div class='ds'>{t(b['desc'])}</div></div>",
                unsafe_allow_html=True,
            )
        st.write("")
