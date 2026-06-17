"""Weight tracking: log, trend line with target, prediction, milestones."""
from __future__ import annotations

from datetime import date

import streamlit as st

from core import database as db
from core import nutrition as N
from core import components as C
from core import state as S
from core import i18n
from core.i18n import t, loc


def render(p: dict) -> None:
    C.section("Weight", "Track the trend, not the day-to-day noise.", "⚖️")
    prof = db.get_profile() or {}
    weights = db.get_weights()
    target = prof.get("target_weight_kg")

    # ---- log entry ----
    with C.card():
        with st.form("log_weight", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            val = c1.number_input(t("Weight (kg)"), 35.0, 300.0,
                                  float(weights[-1]["weight_kg"] if weights else prof.get("weight_kg") or 75.0), 0.1)
            when = c2.date_input(t("Date"), value=date.today(), max_value=date.today())
            if st.form_submit_button(t("💾  Log weight"), type="primary", use_container_width=True):
                db.add_weight(val, when.isoformat())
                S.run_achievement_check()
                st.toast(i18n.tf("Weight logged ✓", "ওজন লেখা হয়েছে ✓"), icon="✅")
                st.rerun()

    if not weights:
        with C.card():
            C.html("<div style='text-align:center'><div style='font-size:2rem'>📈</div>"
                   f"<div class='ns-sub'>{t('Log your first weight to start tracking the trend.')}</div></div>")
        return

    cur = weights[-1]["weight_kg"]
    start = weights[0]["weight_kg"]
    changed = cur - start
    good = (changed < 0 and prof.get("goal") == "Lose weight") or \
           (changed > 0 and prof.get("goal") in ("Gain weight", "Build muscle"))

    C.metric_grid([
        (t("Current"), f"{cur:g} kg", "var(--text)"),
        (t("Start"), f"{start:g} kg", "var(--muted)"),
        (t("Change"), f"{'+' if changed >= 0 else '−'}{abs(changed):.1f} kg",
         "var(--accent)" if good else "var(--carbs)"),
        (t("Target"), f"{target:g} kg" if target else "—", "var(--protein)"),
    ])

    # ---- weight chart ----
    with C.card():
        C.card_title("Weight over time", "Your weigh-ins against your target")
        dates = [date.fromisoformat(w["log_date"]).strftime("%d/%m") for w in weights]
        C.weight_progress_chart(dates, [w["weight_kg"] for w in weights], target, p)

    # ---- prediction / progress to goal ----
    if target:
        pred = N.predict_goal_date(cur, target, prof.get("rate_kg_wk") or 0.5)
        total_to_go = abs(start - target)
        done = abs(start - cur)
        pct = min(100, round(done / total_to_go * 100)) if total_to_go else 100
        with C.card():
            C.card_title("Progress to goal")
            prog_txt = i18n.tf(f"{pct}% there · {abs(cur - target):.1f} kg to go",
                               f"{pct}% হয়েছে · আর {abs(cur - target):.1f} kg বাকি")
            st.progress(pct / 100, text=prog_txt)
            if pred:
                weeks, when = pred
                pace_txt = i18n.tf(
                    f"At your current pace, target reached in ~<b>{weeks} weeks</b> ({when.strftime('%d %b %Y')}).",
                    f"বর্তমান গতিতে চললে প্রায় <b>{weeks} সপ্তাহে</b> লক্ষ্যে পৌঁছাবেন ({when.strftime('%d %b %Y')})।")
                C.html(f"<div class='ns-sub' style='margin-top:8px'>{pace_txt}</div>")
            if abs(cur - target) <= 0.3:
                C.html(f"<div class='ns-toast' style='margin-top:10px'>🏆 {i18n.tf('You have hit your goal weight — incredible work!', 'আপনি লক্ষ্য ওজনে পৌঁছেছেন — অসাধারণ!')}</div>")

    # ---- milestones ----
    if abs(changed) >= 1:
        milestones = list(range(1, int(abs(changed)) + 1))
        sign = "−" if changed < 0 else "+"
        chips = "".join(
            "<span style='display:inline-flex;align-items:center;gap:8px;padding:8px 14px;"
            "border-radius:999px;font-weight:600;font-size:.86rem;background:rgba(0,229,160,.13);"
            "color:var(--accent);border:1px solid rgba(0,229,160,.32)'>"
            f"{sign}{loc(f'{m} kg')}"
            "<span style='display:inline-flex;align-items:center;justify-content:center;"
            "width:18px;height:18px;border-radius:50%;background:var(--accent);color:#04201a;"
            "font-size:.72rem;font-weight:800'>✓</span></span>"
            for m in milestones
        )
        with C.card():
            C.card_title("Milestones", "Every kilogram toward your goal")
            C.html(f"<div style='margin-top:10px;display:flex;flex-wrap:wrap;gap:8px'>{chips}</div>")
