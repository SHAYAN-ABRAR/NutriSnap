"""Nutrition analytics: calorie trends, macro split, fibre, streak heatmap."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from core import database as db
from core import components as C
from core import state as S
from core import gamification as gm
from core import i18n
from core.i18n import t


def render(p: dict) -> None:
    C.section("Analytics", "Spot trends across your week and month.", "📊")

    rng = st.segmented_control("Range", ["7 days", "30 days"], default="7 days",
                               label_visibility="collapsed", format_func=t) or "7 days"
    days = 7 if rng == "7 days" else 30
    data = db.range_totals(days)
    prof = db.get_profile() or {}
    goal = prof.get("calorie_goal") or 2000

    logged_cals = [d["calories"] for d in data if d["calories"] > 0]
    avg = round(sum(logged_cals) / len(logged_cals)) if logged_cals else 0
    on_goal = sum(1 for c in logged_cals if abs(c - goal) <= 150)

    # ---- empty state (#5) ----
    if not logged_cals:
        C.html(f"<div class='ns-empty'><span class='emoji'>📊</span>"
               f"<b>{i18n.tf('No data yet', 'এখনও কোনো ডেটা নেই')}</b><br>"
               f"{i18n.tf('Log a few meals and your trends, macros and streaks will appear here.', 'কিছু খাবার লিখুন — তাহলে আপনার ট্রেন্ড, ম্যাক্রো ও স্ট্রিক এখানে দেখা যাবে।')}</div>")
        if st.button(i18n.tf("➕  Add food", "➕  খাবার যোগ করুন"), use_container_width=True,
                     type="primary", key="an_empty_add"):
            S.go("diary")
        return

    C.metric_grid([
        (t("Avg / day"), f"{avg}", "var(--accent)"),
        (t("Days logged"), f"{len(logged_cals)}/{days}", "var(--protein)"),
        (t("On-target days"), f"{on_goal}", "var(--fiber)"),
        (t("Best streak"), f"{gm.longest_streak()}🔥", "var(--carbs)"),
    ])

    # ---- calorie trend ----
    with C.card():
        C.card_title("Calories vs goal")
        if days == 7:
            C.weekly_bar(data, goal, p)
        else:
            dates = [date.fromisoformat(d["log_date"]).strftime("%d/%m") for d in data]
            C.trend_line(dates, [d["calories"] for d in data], p, target=goal, unit=" kcal")

    # ---- macro split (avg) ----
    tp = sum(d["protein"] for d in data)
    tc = sum(d["carbs"] for d in data)
    tf = sum(d["fat"] for d in data)
    with C.card():
        C.card_title("Average macro split", "Share of calories from each macro")
        if tp + tc + tf > 0:
            C.donut([t("Protein"), t("Carbs"), t("Fat")],
                    [tp * 4, tc * 4, tf * 9],
                    [p["protein"], p["carbs"], p["fat"]], p, height=240)
        else:
            st.caption(t("Log some meals to see your macro breakdown."))

    # ---- protein trend ----
    with C.card():
        C.card_title("Protein intake")
        dlabels = [date.fromisoformat(d["log_date"]).strftime("%d/%m") for d in data]
        C.trend_line(dlabels, [d["protein"] for d in data], p, color=p["protein"],
                     target=prof.get("protein_g"), unit=" g")

    # ---- consistency heatmap ----
    with C.card():
        C.card_title("Consistency · last 5 weeks")
        _heatmap(p, goal)
        heat_txt = i18n.tf(f"Greener = closer to your {goal} kcal goal. Consistency score: ",
                           f"যত সবুজ, তত আপনার {goal} ক্যালরির লক্ষ্যের কাছে। ধারাবাহিকতা স্কোর: ")
        C.html(f"<div class='ns-sub' style='margin-top:8px'>{heat_txt}"
               f"<b style='color:var(--accent)'>{gm.consistency_score(35)}%</b></div>")


def _heatmap(p: dict, goal: int):
    """A compact 5×7 calendar heatmap of recent calorie adherence."""
    totals = {d["log_date"]: d["calories"] for d in db.range_totals(35)}
    today = date.today()
    grid = ""
    for week in range(4, -1, -1):
        row = ""
        for dow in range(7):
            offset = week * 7 + (6 - dow)
            d = (today - timedelta(days=offset)).isoformat()
            cal = totals.get(d, 0)
            if cal == 0:
                color = "var(--surface2)"
            else:
                ratio = min(1.0, cal / goal)
                alpha = 0.3 + ratio * 0.7
                color = f"rgba(0,229,160,{alpha:.2f})"
                if cal > goal * 1.15:
                    color = "rgba(255,107,107,.75)"
            row += (f"<div title='{d}: {int(cal)} kcal' "
                    f"style='width:100%;aspect-ratio:1;border-radius:6px;background:{color}'></div>")
        grid += (f"<div style='display:grid;grid-template-columns:repeat(7,1fr);"
                 f"gap:5px;margin-bottom:5px'>{row}</div>")
    C.html(grid)
