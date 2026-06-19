"""Settings: profile, goals, theme, AI connection, data export, privacy, legal."""
from __future__ import annotations

import json

import streamlit as st

from core import database as db
from core import nutrition as N
from core import ai
from core import components as C
from core import i18n
from core.i18n import t, loc


def render(p: dict) -> None:
    C.section("Settings", "Profile, goals, AI and your data.", "⚙️")
    prof = db.get_profile() or {}

    # ---------------- Profile & goals ----------------
    with st.expander(t("👤  Profile & goals"), expanded=True):
        with st.form("profile_form"):
            name = st.text_input(t("Name"), prof.get("name", ""))
            c1, c2 = st.columns(2)
            sex = c1.selectbox(t("Sex"), ["Male", "Female"], format_func=t,
                               index=0 if (prof.get("sex") or "Male") == "Male" else 1)
            age = c2.number_input(t("Age"), 13, 100, int(prof.get("age") or 28))
            c3, c4 = st.columns(2)
            height = c3.number_input(t("Height (cm)"), 120, 230, int(prof.get("height_cm") or 175))
            weight = c4.number_input(t("Weight (kg)"), 35.0, 250.0, float(prof.get("weight_kg") or 75.0), 0.1)
            activity = st.select_slider(t("Activity"), list(N.ACTIVITY.keys()), format_func=t,
                                        value=prof.get("activity") or "Lightly active")
            goal = st.selectbox(t("Goal"), list(N.GOALS.keys()),
                                index=list(N.GOALS).index(prof.get("goal") or "Maintain"),
                                format_func=lambda x: f"{N.GOALS[x]['emoji']}  {t(x)}")
            c5, c6 = st.columns(2)
            target = c5.number_input(i18n.tf("Target weight (kg)", "লক্ষ্য ওজন (কেজি)"), 40.0, 250.0,
                                     float(prof.get("target_weight_kg") or weight), 0.5)
            _rate = float(prof.get("rate_kg_wk") or 0.5)
            rate = c6.select_slider(i18n.tf("Pace (kg/wk)", "গতি (কেজি/সপ্তাহ)"), [0.25, 0.5, 0.75, 1.0],
                                    value=_rate if _rate in [0.25, 0.5, 0.75, 1.0] else 0.5)
            recompute = st.checkbox(t("Recalculate calorie & macro targets"), value=True)
            if st.form_submit_button(t("Save profile"), type="primary", use_container_width=True):
                new = {**prof, "name": name, "sex": sex, "age": int(age),
                       "height_cm": float(height), "weight_kg": float(weight),
                       "activity": activity, "goal": goal,
                       "target_weight_kg": float(target), "rate_kg_wk": float(rate),
                       "onboarded": 1}
                if recompute:
                    new.update(N.build_targets(new))
                db.save_profile(new)
                st.toast(i18n.tf("Profile saved ✓", "প্রোফাইল সেভ হয়েছে ✓"), icon="✅")
                st.rerun()

    # ---------------- Manual target override ----------------
    with st.expander(t("🎯  Daily targets")):
        with st.form("targets_form"):
            cal = st.number_input(i18n.tf("Calories (kcal)", "ক্যালরি"), 1000, 6000, int(prof.get("calorie_goal") or 2000), 10)
            t1, t2, t3 = st.columns(3)
            pg = t1.number_input(i18n.tf("Protein g", "প্রোটিন গ্রাম"), 0, 400, int(prof.get("protein_g") or 120))
            cg = t2.number_input(i18n.tf("Carbs g", "কার্বস গ্রাম"), 0, 700, int(prof.get("carbs_g") or 200))
            fg = t3.number_input(i18n.tf("Fat g", "ফ্যাট গ্রাম"), 0, 300, int(prof.get("fat_g") or 65))
            wg = st.number_input(i18n.tf("Water (ml)", "পানি (মিলি)"), 500, 6000, int(prof.get("water_goal_ml") or 2500), 50)
            if st.form_submit_button(t("Save targets"), type="primary", use_container_width=True):
                db.save_profile({**prof, "calorie_goal": int(cal), "protein_g": int(pg),
                                 "carbs_g": int(cg), "fat_g": int(fg), "water_goal_ml": int(wg),
                                 "onboarded": 1})
                st.toast(i18n.tf("Targets updated ✓", "লক্ষ্য হালনাগাদ হয়েছে ✓"), icon="✅")
                st.rerun()

    # ---------------- Appearance ----------------
    with st.expander(t("🎨  Appearance")):
        mode = db.get_meta("theme", "dark")
        choice = st.radio(t("Theme"), ["🌙 Dark", "☀️ Light"], format_func=t,
                          index=0 if mode == "dark" else 1, horizontal=True)
        new_mode = "dark" if choice.startswith("🌙") else "light"
        if new_mode != mode:
            db.set_meta("theme", new_mode)
            st.rerun()

        # text size (accessibility) — sets the root font-size multiplier
        scale = float(db.get_meta("text_scale", 1.0) or 1.0)
        sizes = {i18n.tf("A  Normal", "A  স্বাভাবিক"): 1.0,
                 i18n.tf("A+  Large", "A+  বড়"): 1.12,
                 i18n.tf("A++  Larger", "A++  আরও বড়"): 1.25}
        cur_label = next((k for k, v in sizes.items() if abs(v - scale) < 0.01), list(sizes)[0])
        pick = st.radio(i18n.tf("Text size", "লেখার আকার"), list(sizes.keys()),
                        index=list(sizes).index(cur_label), horizontal=True, key="text_size_radio")
        if abs(sizes[pick] - scale) > 0.01:
            db.set_meta("text_scale", sizes[pick])
            st.rerun()

        st.caption(i18n.tf("System theme is set on first run via .streamlit/config.toml; this toggle overrides it live.",
                           "প্রথমবার চালুতে .streamlit/config.toml থেকে থিম ঠিক হয়; এই টগল তা সরাসরি বদলায়।"))

        # Ramadan mode (#11)
        rmd = bool(db.get_meta("ramadan_mode", False))
        new_rmd = st.toggle(i18n.tf("🌙 Ramadan mode (Sehri & Iftar)", "🌙 রমজান মোড (সেহরি ও ইফতার)"),
                            value=rmd, key="ramadan_toggle")
        if new_rmd != rmd:
            db.set_meta("ramadan_mode", new_rmd)
            st.rerun()
        st.caption(i18n.tf("Switches your meal sections to Sehri & Iftar and shows a fasting-friendly banner.",
                           "আপনার খাবারের ভাগগুলো সেহরি ও ইফতারে বদলে দেয় এবং রোজা-বান্ধব ব্যানার দেখায়।"))

    # ---------------- AI connection ----------------
    with st.expander(t("🤖  AI model (Ollama Cloud)")):
        cfg = ai.get_config()
        st.markdown(i18n.tf(
            "Connect an **[Ollama](https://ollama.com)** account (cloud) or a self-hosted "
            "server to enable real photo recognition and full conversational coaching. "
            "Leave blank to use the built-in offline demo.",
            "আসল ছবি শনাক্তকরণ ও পুরো কথোপকথনের কোচিংয়ের জন্য একটি **[Ollama](https://ollama.com)** "
            "অ্যাকাউন্ট (ক্লাউড) বা নিজের সার্ভার যুক্ত করুন। খালি রাখলে অফলাইন ডেমো চলবে।"))
        host = st.text_input(t("Host"), cfg["host"])
        key = st.text_input(t("API key"), cfg["api_key"], type="password",
                            help="Get one at ollama.com → Settings → Keys. Stored locally only.")
        c1, c2 = st.columns(2)
        vmodel = c1.text_input(i18n.tf("Vision model", "ভিশন মডেল"), cfg["vision_model"])
        cmodel = c2.text_input(i18n.tf("Chat model", "চ্যাট মডেল"), cfg["chat_model"])
        b1, b2 = st.columns(2)
        if b1.button(t("Save AI settings"), type="primary", use_container_width=True):
            db.set_meta("ai_config", {"host": host, "api_key": key,
                                      "vision_model": vmodel, "chat_model": cmodel})
            st.toast(i18n.tf("AI settings saved ✓", "এআই সেটিংস সেভ হয়েছে ✓"), icon="✅")
            st.rerun()
        if b2.button(t("Test connection"), use_container_width=True):
            _test_connection(host, key, cmodel)
        status = i18n.tf("🟢 Live", "🟢 লাইভ") if cfg['enabled'] else i18n.tf("🟡 Demo (no key)", "🟡 ডেমো (কী নেই)")
        st.caption(f"{i18n.tf('Status:', 'অবস্থা:')} {status}")

    # ---------------- My custom foods ----------------
    with st.expander(t("🍽️  My foods")):
        customs = db.get_custom_foods()
        if not customs:
            st.caption(i18n.tf("Foods you create in the diary's ✏️ Manual tab (with “Save to My Foods”) "
                               "appear here and in search.",
                               "ডায়েরির ✏️ নিজে লিখুন ট্যাবে (“আমার খাবার-এ সেভ করুন” দিয়ে) তৈরি খাবার "
                               "এখানে ও খোঁজায় আসবে।"))
        for f in customs:
            cc1, cc2 = st.columns([5, 1])
            cc_cals = loc(f"{int(f['calories'])} kcal")
            cc1.markdown(
                f"<div style='display:flex;align-items:center;padding-top:4px'>{C.food_icon(f, 34)}"
                f"<div><b>{t(f['name'])}</b><br><span class='ns-sub'>"
                f"{cc_cals} · {loc(f['unit'])}</span></div></div>",
                unsafe_allow_html=True,
            )
            if cc2.button("🗑", key=f"delcf_{f['name']}", use_container_width=True):
                db.delete_custom_food(f["name"])
                st.rerun()

    # ---------------- Data & privacy ----------------
    with st.expander(t("🔒  Data & privacy")):
        st.markdown(i18n.tf(
            "All your data lives in a local SQLite file on this device "
            "(`data/nutrisnap.db`). There are no accounts and nothing is sent to a server "
            "— except food photos/messages you choose to send to your configured AI model.",
            "আপনার সব ডেটা এই ডিভাইসের একটি লোকাল SQLite ফাইলে (`data/nutrisnap.db`) থাকে। "
            "কোনো অ্যাকাউন্ট নেই, সার্ভারে কিছু যায় না — শুধু আপনি যে ছবি/বার্তা এআই মডেলে পাঠান তা ছাড়া।"))
        export = json.dumps(db.export_all(), indent=2, default=str)
        st.download_button(i18n.tf("⬇️  Export my data (JSON)", "⬇️  আমার ডেটা রপ্তানি করুন (JSON)"), export,
                           file_name="nutrisnap-export.json", mime="application/json",
                           use_container_width=True)

        st.divider()
        st.markdown(f"**{t('Danger zone')}**")
        if st.checkbox(t("I understand this cannot be undone"), key="danger"):
            d1, d2 = st.columns(2)
            if d1.button(t("Clear all logs"), use_container_width=True):
                db.wipe_logs()
                st.toast(i18n.tf("Logs cleared", "লগ মুছে ফেলা হয়েছে"), icon="🧹")
                st.rerun()
            if d2.button(t("Reset everything"), use_container_width=True):
                db.wipe_everything()
                st.session_state.clear()
                st.rerun()

    # ---------------- Legal ----------------
    with st.expander(t("📄  Privacy policy & terms")):
        st.markdown(i18n.tf(
            """
**Privacy.** NutriSnap is local-first. Your profile, food logs, weight, water and chat
history are stored only on this device. We do not collect, sell, or transmit your data.
If you connect an AI provider, the images and messages you submit are sent to that
provider solely to generate a response, subject to their policy.

**Health disclaimer.** NutriSnap provides estimates for general wellness and education.
It is **not** medical advice. Calorie and macro figures (especially AI photo estimates)
are approximations. Consult a qualified professional before making significant dietary
or health changes.

**Terms.** Provided "as is", without warranty. You are responsible for verifying the
accuracy of logged information.
            """,
            """
**গোপনীয়তা।** NutriSnap লোকাল-ফার্স্ট। আপনার প্রোফাইল, খাবারের লগ, ওজন, পানি ও চ্যাট
ইতিহাস কেবল এই ডিভাইসেই থাকে। আমরা আপনার ডেটা সংগ্রহ, বিক্রি বা পাঠাই না। আপনি কোনো
এআই প্রোভাইডার যুক্ত করলে, আপনার দেওয়া ছবি ও বার্তা কেবল উত্তর তৈরির জন্য সেই প্রোভাইডারে যায়।

**স্বাস্থ্য সতর্কতা।** NutriSnap সাধারণ সুস্থতা ও শিক্ষার জন্য আনুমানিক হিসাব দেয়। এটি
চিকিৎসা পরামর্শ **নয়**। ক্যালরি ও ম্যাক্রোর হিসাব (বিশেষত এআই ছবির অনুমান) আনুমানিক।
বড় কোনো খাদ্যাভ্যাস বা স্বাস্থ্যগত পরিবর্তনের আগে বিশেষজ্ঞের পরামর্শ নিন।

**শর্তাবলি।** "যেমন আছে" ভিত্তিতে, কোনো ওয়ারেন্টি ছাড়া। লেখা তথ্যের সঠিকতা যাচাইয়ের
দায়িত্ব আপনার।
            """))
        st.caption(i18n.tf("NutriSnap · v1.0 · Local-first AI nutrition tracker",
                           "NutriSnap · v1.0 · লোকাল-ফার্স্ট এআই পুষ্টি ট্র্যাকার"))


def _test_connection(host, key, model):
    if not key:
        st.warning("No API key set — running in demo mode.")
        return
    try:
        import requests
        headers = {"Authorization": f"Bearer {key}"}
        r = requests.post(f"{host.rstrip('/')}/api/chat",
                          headers=headers,
                          json={"model": model, "stream": False,
                                "messages": [{"role": "user", "content": "Reply with: OK"}]},
                          timeout=30)
        r.raise_for_status()
        st.success(f"🟢 Connected — {model} responded.")
    except Exception as e:
        st.error(f"Connection failed: {type(e).__name__} — {e}")
