"""
NutriSnap — AI-powered, local-first calorie & nutrition tracker.

Single-file router for a mobile-first Streamlit app. Run with:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="NutriSnap — AI Calorie Tracker",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"about": "NutriSnap · local-first AI nutrition tracker · v1.0"},
)

from core import database as db          # noqa: E402
from core import components as C         # noqa: E402
from core import i18n                    # noqa: E402
from core.i18n import t                  # noqa: E402
from views import (                      # noqa: E402
    onboarding, dashboard, diary, scan, analytics,
    weight, water, coach, achievements, settings,
)

# Primary nav: (page_key, material-icon, label). Center item (Scan) renders as a FAB.
PRIMARY_NAV = [
    ("dashboard", ":material/home:", "Home"),
    ("diary", ":material/menu_book:", "Diary"),
    ("scan", ":material/photo_camera:", "Scan"),
    ("coach", ":material/forum:", "Coach"),
    ("more", ":material/more_horiz:", "More"),
]
SECONDARY = {"analytics", "weight", "water", "achievements", "settings", "more"}

RENDERERS = {
    "dashboard": dashboard.render, "diary": diary.render, "scan": scan.render,
    "coach": coach.render, "analytics": analytics.render, "weight": weight.render,
    "water": water.render, "achievements": achievements.render,
    "settings": settings.render,
}


def main() -> None:
    db._conn()                                   # ensure schema exists
    palette = C.inject_theme()                   # paint design system
    st.session_state.setdefault("page", "dashboard")

    # ---- onboarding gate ----
    if not db.is_onboarded():
        onboarding.render(palette)
        return

    _header()
    _celebrations()

    page = st.session_state.page
    if page == "more":
        _more_menu()
    else:
        RENDERERS.get(page, dashboard.render)(palette)

    _nav(page)


def _header() -> None:
    c1, c2 = st.columns([3, 1.1], vertical_alignment="center")
    with c1:
        C.html(
            "<div style='font-family:Space Grotesk;font-weight:700;font-size:1.25rem'>"
            "<span class='ns-grad'>Nutri</span><span>Snap</span></div>"
        )
    with c2:
        # Language toggle — label shows the language you'll switch TO.
        switch_to = "বাংলা" if i18n.get_lang() == "en" else "English"
        if st.button(f"🌐 {switch_to}", key="lang_toggle", use_container_width=True,
                     help="English ⇄ বাংলা (ঢাকাইয়া)"):
            i18n.toggle_lang()
            st.rerun()
    C.html("<div style='height:6px'></div>")


def _celebrations() -> None:
    if st.session_state.pop("just_onboarded", False):
        st.toast(i18n.tf("Welcome to NutriSnap! Let's log your first meal 🎉",
                         "NutriSnap-এ স্বাগতম! চলুন প্রথম খাবারটা যোগ করি 🎉"), icon="🎉")
    pending = st.session_state.pop("pending_celebrations", [])
    if pending:
        C.celebrate(pending)


def _more_menu() -> None:
    C.section("More", "Everything else, one tap away.", "⋯")
    tiles = [
        ("analytics", "📊", "Analytics", "Trends, macros, heatmap"),
        ("weight", "⚖️", "Weight", "Log & predict progress"),
        ("water", "💧", "Hydration", "Track daily water"),
        ("achievements", "🏆", "Achievements", "Streaks, levels, badges"),
        ("settings", "⚙️", "Settings", "Profile, goals, AI, data"),
    ]
    for key, icon, title, sub in tiles:
        if st.button(f"{icon}  {t(title)}", use_container_width=True, key=f"more_{key}"):
            st.session_state.page = key
            st.rerun()
        C.html(f"<div class='ns-sub' style='margin:-6px 0 10px 6px'>{t(sub)}</div>")


def _nav(active: str) -> None:
    C.html("<div class='ns-navmark'></div>")
    cols = st.columns(len(PRIMARY_NAV))
    for col, (key, icon, label) in zip(cols, PRIMARY_NAV):
        is_active = key == active or (key == "more" and active in SECONDARY)
        # Material icon + label; the Scan button (key nav_scan) is styled into a FAB via CSS.
        if col.button(t(label), icon=icon, key=f"nav_{key}", use_container_width=True,
                      type="primary" if is_active else "secondary"):
            if st.session_state.page != key:
                st.session_state.page = key
                st.rerun()


if __name__ == "__main__":
    main()
