"""AI food recognition: capture/upload a photo, analyze, edit, save to diary."""
from __future__ import annotations

import time

import streamlit as st

from core import ai
from core import database as db
from core import components as C
from core import state as S
from core import i18n
from core.i18n import t, loc


def render(p: dict) -> None:
    C.section("AI Food Scan", "Point, shoot, and let AI estimate the nutrition.", "📸")

    live = ai.is_live()
    badge = (f"<span class='ns-pill accent'>{t('● Live AI')}</span>" if live
             else f"<span class='ns-pill'>{t('● Demo mode')}</span>")
    sub = t("Cloud vision model connected") if live else t("Add an Ollama key in Settings for real recognition")
    C.html(f"<div style='margin-bottom:8px'>{badge} <span class='ns-sub'>{sub}</span></div>")

    tab_cam, tab_up = st.tabs([t("📷 Camera"), t("🖼️ Upload")])
    image_bytes = None
    with tab_cam:
        shot = st.camera_input(i18n.tf("Take a photo of your meal", "আপনার খাবারের ছবি তুলুন"),
                               label_visibility="collapsed")
        if shot:
            image_bytes = shot.getvalue()
    with tab_up:
        up = st.file_uploader(i18n.tf("Upload food photo(s)", "খাবারের ছবি আপলোড করুন"),
                              type=["jpg", "jpeg", "png", "webp"],
                              accept_multiple_files=False, label_visibility="collapsed")
        if up:
            image_bytes = up.getvalue()

    # New image -> reset previous analysis
    if image_bytes and st.session_state.get("scan_hash") != hash(image_bytes):
        st.session_state.scan_hash = hash(image_bytes)
        st.session_state.scan_result = None
        st.session_state.scan_bytes = image_bytes

    if st.session_state.get("scan_bytes"):
        with C.card():
            st.image(st.session_state.scan_bytes, use_container_width=True)

        if st.session_state.get("scan_result") is None:
            if st.button(t("✨  Analyze with AI"), type="primary", use_container_width=True):
                _run_analysis(st.session_state.scan_bytes)
                st.rerun()
        else:
            _show_results(p)


def _run_analysis(image_bytes: bytes) -> None:
    steps = ["Detecting food items…", "Estimating portions…",
             "Calculating macros…", "Scoring confidence…"]
    bar = st.progress(0, text=steps[0])
    for i, s in enumerate(steps):
        bar.progress(int((i + 1) / len(steps) * 90), text=s)
        time.sleep(0.35)
    result = ai.analyze_food(image_bytes)
    bar.progress(100, text="Done ✓")
    time.sleep(0.2)
    bar.empty()
    st.session_state.scan_result = result
    st.session_state.has_scanned = True


def _show_results(p: dict) -> None:
    res = st.session_state.scan_result
    foods = res["foods"]
    C.html(f"<div class='ns-toast' style='margin-bottom:10px'>{'🟢' if res['live'] else '🟡'} {res['note']}</div>")

    if not foods:
        st.warning(t("No foods detected. Try a clearer, closer photo."))
        return

    C.section("Detected foods", "Review and tweak — your edits are saved, not the guess.")
    meal = st.selectbox(t("Add to meal"), [m for m, _ in S.meals()],
                        index=_meal_guess(), format_func=t)

    edited = []
    for i, f in enumerate(foods):
        conf = int(f.get("confidence", 0.75) * 100)
        conf_col = "var(--accent)" if conf >= 80 else ("var(--carbs)" if conf >= 65 else "var(--warn)")
        with C.card():
            C.html(
                f"<div style='display:flex;justify-content:space-between;align-items:center'>"
                f"<div class='ns-h'>{f['emoji']} {t(f['name'])}</div>"
                f"<span class='ns-pill' style='color:{conf_col};border-color:{conf_col}'>{i18n.tf(f'{conf}% sure', f'{conf}% নিশ্চিত')}</span></div>"
                f"<div class='ns-sub'>{loc(f.get('unit','1 serving'))}</div>"
            )
            c1, c2, c3, c4, c5 = st.columns(5)
            cal = c1.number_input(t("kcal"), 0, 3000, int(f["calories"]), key=f"cal{i}", help="Calories")
            pro = c2.number_input("P", 0, 300, int(f["protein"]), key=f"pro{i}", help="Protein (g)")
            car = c3.number_input("C", 0, 400, int(f["carbs"]), key=f"car{i}", help="Carbohydrates (g)")
            fat = c4.number_input("F", 0, 200, int(f["fat"]), key=f"fat{i}", help="Fat (g)")
            fib = c5.number_input("Fib", 0, 100, int(f["fiber"]), key=f"fib{i}", help="Fiber (g)")
            keep = st.checkbox(t("Include"), value=True, key=f"keep{i}")
        if keep:
            edited.append({**f, "calories": cal, "protein": pro, "carbs": car,
                           "fat": fat, "fiber": fib})

    total = sum(e["calories"] for e in edited)
    total_lbl = i18n.tf("TOTAL TO ADD", "যোগ করার মোট")
    items_lbl = i18n.tf(f"{len(edited)} item(s) → {meal}", f"{len(edited)} টি → {t(meal)}")
    C.html(f"<div class='ns-card' style='text-align:center'><div class='ns-sub'>{total_lbl}</div>"
           f"<div class='ns-big ns-grad'>{loc(f'{int(total)} kcal')}</div>"
           f"<div class='ns-sub'>{items_lbl}</div></div>")

    b1, b2 = st.columns([1, 2])
    if b1.button(t("Discard"), use_container_width=True):
        _clear()
        st.rerun()
    if b2.button(t("💾  Save to diary"), type="primary", use_container_width=True, disabled=not edited):
        for e in edited:
            db.add_food(meal, {**e, "source": e.get("source", "ai_vision")})
        S.run_achievement_check()
        _clear()
        st.toast(i18n.tf(f"Added {len(edited)} item(s) to {meal} ✓",
                         f"{len(edited)} টি {t(meal)}-এ যোগ হয়েছে ✓"), icon="✅")
        S.go("diary")


def _meal_guess() -> int:
    import datetime as dt
    h = dt.datetime.now().hour
    if h < 11:
        return 0
    if h < 15:
        return 1
    if h < 21:
        return 2
    return 3


def _clear():
    for k in ("scan_bytes", "scan_result", "scan_hash"):
        st.session_state.pop(k, None)
