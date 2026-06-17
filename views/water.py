"""Water tracking: one-tap logging, daily ring, custom amounts, weekly history."""
from __future__ import annotations

from datetime import date

import streamlit as st
import plotly.graph_objects as go

from core import database as db
from core import components as C
from core import state as S
from core import i18n
from core.i18n import t, loc


def render(p: dict) -> None:
    C.section("Hydration", "Small sips add up. Stay on top of your daily goal.", "💧")
    prof = db.get_profile() or {}
    goal = prof.get("water_goal_ml") or 2500
    have = db.water_today()
    pct = round(have / max(1, goal) * 100)

    with C.card():
        C.mini_ring(have, goal, p, p["water"], "ml", "ml", height=210)
        cap = i18n.tf(f"{pct}% of your daily goal · ~{round(have/250)} glasses",
                      f"প্রতিদিনের লক্ষ্যের {pct}% · প্রায় {round(have/250)} গ্লাস")
        C.html(f"<div style='text-align:center'><div class='ns-big' style='font-size:1.6rem'>{loc(str(have))} "
               f"<span style='font-size:1rem;color:var(--muted)'>{loc(f'/ {goal} ml')}</span></div>"
               f"<div class='ns-sub'>{cap}</div></div>")

    if have >= goal:
        C.html(f"<div class='ns-toast' style='margin-bottom:12px'>💧 {t('Goal reached — nicely hydrated today!')}</div>")

    # ---- one-tap quick adds ----
    C.section("Quick add")
    q = st.columns(4)
    for col, (label, ml) in zip(q, [("🥃 150", 150), ("🥤 250", 250),
                                    ("🍶 500", 500), ("🍼 750", 750)]):
        if col.button(loc(label), use_container_width=True, key=f"w{ml}"):
            db.add_water(ml)
            S.run_achievement_check()
            st.rerun()

    # ---- custom amount ----
    with st.expander(t("Custom amount")):
        c1, c2 = st.columns([3, 1])
        amt = c1.number_input("ml", 50, 2000, 300, 50, label_visibility="collapsed")
        if c2.button(t("Add"), use_container_width=True, type="primary"):
            db.add_water(int(amt))
            S.run_achievement_check()
            st.rerun()
    if st.button(t("↺ Reset today"), use_container_width=True):
        db.reset_water_today()
        st.rerun()

    # ---- weekly history ----
    with C.card():
        C.card_title("Last 7 days")
        data = db.water_range(7)
        labels = [date.fromisoformat(d["log_date"]).strftime("%a") for d in data]
        colors = [p["water"] if d["amount_ml"] >= goal else C._rgba(p["water"], 0.45) for d in data]
        fig = go.Figure(go.Bar(x=labels, y=[d["amount_ml"] for d in data],
                               marker_color=colors, width=0.6,
                               hovertemplate="%{y} ml<extra></extra>"))
        fig.add_hline(y=goal, line_dash="dot", line_color=p["muted"])
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(showgrid=False)
        C._style(fig, p, 200)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
