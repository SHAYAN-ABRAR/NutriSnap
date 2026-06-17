"""Multi-step onboarding: collects the profile and computes personalized targets."""
from __future__ import annotations

import streamlit as st

from core import database as db
from core import nutrition as N
from core import components as C
from core import i18n
from core.i18n import t


def render(p: dict) -> None:
    ss = st.session_state
    ss.setdefault("onb_step", 0)
    step = ss.onb_step
    total = 4

    # ---- hero / progress ----
    C.html(
        "<div style='text-align:center;margin:6px 0 2px'>"
        "<div class='ns-big ns-grad' style='font-size:2.2rem'>NutriSnap</div>"
        f"<div class='ns-sub'>{t('AI nutrition tracking that feels effortless')}</div></div>"
    )
    st.progress((step) / total, text=i18n.tf(f"Step {min(step + 1, total)} of {total}",
                                             f"ধাপ {min(step + 1, total)} / {total}"))

    if step == 0:
        _welcome()
    elif step == 1:
        _about_you()
    elif step == 2:
        _activity_goal()
    elif step == 3:
        _summary(p)


def _next():
    st.session_state.onb_step += 1
    st.rerun()


def _back():
    st.session_state.onb_step -= 1
    st.rerun()


def _welcome():
    body = i18n.tf(
        "Snap a photo of your meal and let AI estimate the calories and macros. "
        "Track your weight, water and habits — all stored privately on your device, "
        "no account required.",
        "আপনার খাবারের একটি ছবি তুলুন, এআই ক্যালরি ও ম্যাক্রোর হিসাব করে দেবে। "
        "ওজন, পানি ও অভ্যাস ট্র্যাক করুন — সব আপনার ডিভাইসেই গোপনে থাকে, কোনো অ্যাকাউন্ট লাগে না।")
    pills = i18n.tf(
        "<span class='ns-pill accent'>📸 AI food scan</span>"
        "<span class='ns-pill'>📊 Smart analytics</span>"
        "<span class='ns-pill'>🔥 Streaks</span>"
        "<span class='ns-pill'>🔒 100% local</span>",
        "<span class='ns-pill accent'>📸 এআই ফুড স্ক্যান</span>"
        "<span class='ns-pill'>📊 স্মার্ট অ্যানালিটিক্স</span>"
        "<span class='ns-pill'>🔥 স্ট্রিক</span>"
        "<span class='ns-pill'>🔒 ১০০% লোকাল</span>")
    C.html(
        "<div class='ns-card'>"
        f"<div class='ns-h' style='font-size:1.3rem'>{t('Welcome 👋')}</div>"
        f"<p style='color:var(--muted);margin-top:8px;line-height:1.5'>{body}</p>"
        f"<div style='display:flex;gap:8px;flex-wrap:wrap;margin-top:12px'>{pills}</div></div>"
    )
    if st.button(t("Get started  →"), type="primary", use_container_width=True):
        _next()


def _about_you():
    d = db.get_profile() or {}
    with st.container():
        C.section("About you", "We use this to calculate your calorie needs.")
        name = st.text_input(t("Name"), value=d.get("name", ""), placeholder=i18n.tf("e.g. Alex", "যেমন রহিম"))
        c1, c2 = st.columns(2)
        sex = c1.selectbox(t("Sex"), ["Male", "Female"], format_func=t,
                           index=0 if (d.get("sex") or "Male") == "Male" else 1)
        age = c2.number_input(t("Age"), 13, 100, int(d.get("age") or 28))
        c3, c4 = st.columns(2)
        height = c3.number_input(t("Height (cm)"), 120, 230, int(d.get("height_cm") or 175))
        weight = c4.number_input(t("Weight (kg)"), 35.0, 250.0, float(d.get("weight_kg") or 75.0), 0.1)

    b1, b2 = st.columns([1, 2])
    if b1.button(t("← Back"), use_container_width=True):
        _back()
    if b2.button(t("Continue  →"), type="primary", use_container_width=True):
        db.save_profile({**d, "name": name or "Friend", "sex": sex, "age": int(age),
                         "height_cm": float(height), "weight_kg": float(weight),
                         "onboarded": 0})
        _next()


def _activity_goal():
    d = db.get_profile() or {}
    C.section("Your goal", "Pick a goal and how active you are.")

    acts = list(N.ACTIVITY.keys())
    activity = st.select_slider(
        t("Activity level"), options=acts, format_func=t,
        value=d.get("activity") or "Lightly active",
    )
    st.caption(t(N.ACTIVITY[activity][1]))

    goal = st.radio(
        t("Your goal"), list(N.GOALS.keys()),
        index=list(N.GOALS).index(d.get("goal") or "Lose weight"),
        format_func=lambda x: f"{N.GOALS[x]['emoji']}  {t(x)}",
        horizontal=False,
    )

    cur_w = float(d.get("weight_kg") or 75.0)
    target = cur_w
    rate = float(d.get("rate_kg_wk") or 0.5)
    if goal in ("Lose weight", "Gain weight", "Build muscle"):
        default_target = d.get("target_weight_kg") or (cur_w + (-5 if goal == "Lose weight" else 5))
        target = st.number_input(t("Target weight (kg)"), 40.0, 250.0, float(default_target), 0.5)
        rate = st.select_slider(t("Weekly pace (kg/week)"),
                                options=[0.25, 0.5, 0.75, 1.0], value=rate if rate in [0.25, 0.5, 0.75, 1.0] else 0.5)

    b1, b2 = st.columns([1, 2])
    if b1.button(t("← Back"), use_container_width=True):
        _back()
    if b2.button(t("See my plan  →"), type="primary", use_container_width=True):
        prof = {**d, "activity": activity, "goal": goal,
                "target_weight_kg": float(target), "rate_kg_wk": float(rate)}
        prof.update(N.build_targets(prof))
        db.save_profile({**prof, "onboarded": 0})
        _next()


def _summary(_):
    d = db.get_profile() or {}
    C.section("Your personalized plan ✨", "Tuned to your body and goal. Editable anytime in Settings.")

    goal_key = d.get('goal') or 'Maintain'
    cals = d.get("calorie_goal") or 2000
    target_lbl = i18n.tf("DAILY CALORIE TARGET", "প্রতিদিনের ক্যালরি লক্ষ্য")
    per_day = i18n.tf(f"kcal / day · {N.GOALS[goal_key]['emoji']} {goal_key}",
                      f"ক্যালরি / দিন · {N.GOALS[goal_key]['emoji']} {t(goal_key)}")
    C.html(
        "<div class='ns-card' style='text-align:center'>"
        f"<div class='ns-sub'>{target_lbl}</div>"
        f"<div class='ns-big ns-grad' style='font-size:2.8rem;margin:6px 0'>{cals}</div>"
        f"<div class='ns-sub'>{per_day}</div>"
        "</div>"
    )
    C.metric_grid([
        (t("Protein"), f"{d.get('protein_g') or 0} g", "var(--protein)"),
        (t("Carbs"), f"{d.get('carbs_g') or 0} g", "var(--carbs)"),
        (t("Fat"), f"{d.get('fat_g') or 0} g", "var(--fat)"),
        (t("Water"), f"{d.get('water_goal_ml') or 0} ml", "var(--water)"),
    ])

    pred = N.predict_goal_date(d.get("weight_kg") or 75, d.get("target_weight_kg"),
                              d.get("rate_kg_wk") or 0.5)
    if pred:
        weeks, when = pred
        plan_txt = i18n.tf(
            f"🎯 At {d.get('rate_kg_wk')} kg/week you could reach "
            f"<b>{d.get('target_weight_kg')} kg</b> in about <b>{weeks} weeks</b> "
            f"(~{when.strftime('%d %b %Y')}).",
            f"🎯 সপ্তাহে {d.get('rate_kg_wk')} কেজি হারে আপনি প্রায় <b>{weeks} সপ্তাহে</b> "
            f"<b>{d.get('target_weight_kg')} কেজি</b> ছুঁতে পারেন (~{when.strftime('%d %b %Y')})।")
        C.html(f"<div class='ns-toast' style='margin-top:14px'>{plan_txt}</div>")

    st.write("")
    b1, b2 = st.columns([1, 2])
    if b1.button(t("← Back"), use_container_width=True):
        _back()
    if b2.button(t("Start tracking  🚀"), type="primary", use_container_width=True):
        db.save_profile({**d, "onboarded": 1})
        st.session_state.onb_step = 0
        st.session_state.page = "dashboard"
        st.session_state.just_onboarded = True
        st.rerun()
