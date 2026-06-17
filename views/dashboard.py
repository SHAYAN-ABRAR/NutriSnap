"""Home dashboard: calorie ring, macros, water, weight trend and quick actions."""
from __future__ import annotations

import streamlit as st

from core import database as db
from core import components as C
from core import gamification as gm
from core import state as S
from core import i18n
from core.i18n import t, loc


def render(p: dict) -> None:
    ctx = S.daily_context()
    prof = ctx["profile"]
    name = prof.get("name") or "there"
    greeting = _greeting()
    streak = ctx["streak"]

    # ---- greeting + streak ----
    streak_lbl = i18n.tf(f"{streak}-day streak", f"{streak} দিনের স্ট্রিক")
    C.html(
        f"<div style='display:flex;justify-content:space-between;align-items:center'>"
        f"<div><div class='ns-sub'>{t(greeting)}</div>"
        f"<div class='ns-h' style='font-size:1.35rem'>{name} 👋</div></div>"
        f"<div class='ns-pill accent'><span class='flame'>🔥</span> {streak_lbl}</div></div>"
    )

    # ---- hero calorie ring ----
    with C.card():
        C.calorie_ring(ctx["consumed"], ctx["calorie_goal"], p)
        cols = st.columns(3)
        _stat(cols[0], t("Goal"), f"{ctx['calorie_goal']}", "var(--text)")
        _stat(cols[1], t("Food"), f"{int(ctx['consumed'])}", "var(--accent)")
        _stat(cols[2], t("Left"), f"{int(max(0, ctx['remaining']))}", "var(--protein)")

    # ---- quick actions ----
    a1, a2 = st.columns(2)
    if a1.button(f"📸  {t('Scan a meal')}", use_container_width=True, type="primary"):
        S.go("scan")
    if a2.button(f"➕  {t('Add food')}", use_container_width=True):
        S.go("diary")

    # ---- macros (pure-HTML card, self-contained) ----
    C.macro_bars(ctx, {"protein_g": ctx["protein_goal"], "carbs_g": ctx["carbs_goal"],
                       "fat_g": ctx["fat_goal"], "fiber_g": 30}, p)

    # ---- expandable "what you ate" breakdown ----
    _food_breakdown(ctx)

    # ---- water + weight side by side ----
    w1, w2 = st.columns(2)
    with w1:
        with C.card():
            C.html(f"<div class='ns-h' style='text-align:center'>{t('💧 Water')}</div>")
            C.mini_ring(ctx["water"], ctx["water_goal"], p, p["water"], "ml", "ml", height=140)
            pct = round(ctx["water"] / max(1, ctx["water_goal"]) * 100)
            wcap = i18n.tf(f"{pct}% of {ctx['water_goal']} ml", f"{ctx['water_goal']} ml-এর {pct}%")
            C.html(f"<div class='ns-sub' style='text-align:center'>{wcap}</div>")
            if st.button("+250 ml", use_container_width=True, key="dash_water"):
                db.add_water(250)
                S.run_achievement_check()
                st.rerun()
    with w2:
        with C.card():
            C.html(f"<div class='ns-h' style='text-align:center'>{t('⚖️ Weight')}</div>")
            weights = db.get_weights()
            target = prof.get("target_weight_kg")
            if weights:
                cur = weights[-1]["weight_kg"]
                start = weights[0]["weight_kg"]
            else:
                cur = prof.get("weight_kg")
                start = cur
            if cur is not None:
                C.weight_ring(cur, start, target, p, height=140)
                delta = cur - (start if start is not None else cur)
                arrow = "▼" if delta < 0 else ("▲" if delta > 0 else "•")
                good = (delta < 0 and ctx["goal"] == "Lose weight") or \
                       (delta > 0 and ctx["goal"] in ("Gain weight", "Build muscle"))
                col = "var(--accent)" if good else "var(--muted)"
                if target and abs(cur - target) < 0.3:
                    mark = f"<span style='color:var(--accent)'>🎯 {t('Target reached')}</span>"
                elif target:
                    togo = i18n.tf(f"{abs(cur - target):.1f} kg to {target:g} kg",
                                   f"{target:g} kg-এর {abs(cur - target):.1f} kg বাকি")
                    since = i18n.tf(f"{abs(delta):.1f} since start", f"শুরু থেকে {abs(delta):.1f}")
                    mark = f"{togo} · <span style='color:{col}'>{arrow} {since}</span>"
                else:
                    since = i18n.tf(f"{abs(delta):.1f} kg since start", f"শুরু থেকে {abs(delta):.1f} kg")
                    mark = f"<span style='color:{col}'>{arrow} {since}</span>"
                C.html(f"<div class='ns-sub' style='text-align:center'>{mark}</div>")
            else:
                C.html(f"<div class='ns-sub' style='margin:22px 0;text-align:center'>{t('No weight logged yet')}</div>")
            if st.button(t("Log weight"), use_container_width=True, key="dash_weight"):
                S.go("weight")

    # ---- consistency / level ----
    lvl = gm.level_for(gm.total_xp())
    with C.card():
        C.html(
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<div class='ns-h'>{lvl['name']} · Lvl {lvl['level']}</div>"
            f"<div class='ns-sub'>{lvl['xp']} XP</div></div>"
        )
        next_txt = i18n.tf(f"{lvl['next_at'] - lvl['xp']} XP to next level",
                           f"পরের লেভেলে {lvl['next_at'] - lvl['xp']} XP বাকি")
        st.progress(lvl["progress"] / 100, text=t("Max level 🎉") if lvl["is_max"] else next_txt)
        C.html(f"<div class='ns-sub'>{t('Consistency (14 days):')} "
               f"<b style='color:var(--accent)'>{gm.consistency_score()}%</b></div>")

    S.run_achievement_check()


MEAL_ORDER = [("Breakfast", "🌅"), ("Lunch", "🌞"), ("Dinner", "🌙"), ("Snacks", "🍪")]


def _food_breakdown(ctx: dict) -> None:
    """Expandable list of today's foods and how they add up to your macros."""
    foods = db.get_foods()
    exp_label = i18n.tf(f"🍽️  See what you ate today · {ctx['items']} item(s)",
                        f"🍽️  আজ কী খেয়েছেন দেখুন · {ctx['items']} টি")
    with st.expander(exp_label):
        if not foods:
            st.caption(t("Nothing logged yet today. Scan or add a meal to see the breakdown."))
            return
        by_meal: dict[str, list] = {}
        for f in foods:
            by_meal.setdefault(f["meal"], []).append(f)
        for meal, emoji in MEAL_ORDER:
            items = by_meal.get(meal)
            if not items:
                continue
            meal_cals = sum(i["calories"] * i["qty"] for i in items)
            C.html(f"<div class='ns-sub' style='margin:8px 0 2px'><b>{emoji} {t(meal)}</b> · "
                   f"{loc(f'{int(meal_cals)} kcal')}</div>")
            for it in items:
                q = it["qty"] or 1
                qlabel = f" <span class='ns-sub'>×{loc(f'{q:g}')}</span>" if q != 1 else ""
                kc = loc(f"{int(it['calories'] * q)} kcal")
                pr = loc(f"{int(it['protein'] * q)}g")
                cb = loc(f"{int(it['carbs'] * q)}g")
                ft = loc(f"{int(it['fat'] * q)}g")
                fb = loc(f"{int(it['fiber'] * q)}g")
                C.html(
                    f"<div class='ns-food'><div style='display:flex;align-items:center'>"
                    f"{C.food_icon(it, 30)}<div>"
                    f"<b>{t(it['name'])}</b>{qlabel}<br>"
                    f"<span class='ns-sub'>{kc} · {pr} {t('protein')} · {cb} {t('carbs')} · "
                    f"{ft} {t('fat')} · {fb} {t('fiber')}</span></div></div></div>"
                )
        if st.button(t("Open full diary  →"), use_container_width=True, key="macro_to_diary"):
            S.go("diary")


def _greeting() -> str:
    import datetime as dt
    h = dt.datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 18:
        return "Good afternoon"
    return "Good evening"


def _stat(col, label, value, color):
    col.markdown(
        f"<div style='text-align:center'><div class='ns-sub'>{label}</div>"
        f"<div style='font-family:Space Grotesk;font-weight:700;font-size:1.25rem;color:{color}'>{loc(str(value))}</div></div>",
        unsafe_allow_html=True,
    )
