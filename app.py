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

    # clicking the brand wordmark links to ?p=home → route to the dashboard
    if st.query_params.get("p") == "home":
        st.session_state.page = "dashboard"
        st.query_params.clear()

    _topbar()                                    # persistent top bar (logo + language)

    # ---- onboarding gate ----
    if not db.is_onboarded():
        onboarding.render(palette)
        return

    _celebrations()

    page = st.session_state.page
    if page == "more":
        _more_menu()
    else:
        RENDERERS.get(page, dashboard.render)(palette)

    _nav(page)


def _topbar() -> None:
    """Fixed top bar (mirrors the bottom nav): brand on the left, then the
    language and theme toggles on the right. The .ns-topmark marker pins the
    next row to the top."""
    C.html("<div class='ns-topmark'></div>")
    c1, c2, c3 = st.columns([5, 1.3, 0.95], vertical_alignment="center")
    with c1:
        # the wordmark is a plain HTML link to Home (no button); clicking it sets
        # ?p=home, which main() reads to route back to the dashboard.
        C.html(
            "<a href='?p=home' target='_self' "
            "style='text-decoration:none;color:var(--text);display:inline-block;cursor:pointer'>"
            "<div style='font-family:Space Grotesk;font-weight:700;font-size:1.2rem;line-height:1'>"
            "<span class='ns-grad'>Nutri</span><span>Snap</span></div></a>"
        )
    with c2:
        _lang_toggle()
    with c3:
        _theme_toggle()


def _lang_toggle() -> None:
    """One-tap language toggle: the pill shows the active language and flips it on
    every click (English ⇄ বাংলা)."""
    label = "🌐 EN" if i18n.get_lang() == "en" else "🌐 বাং"
    if st.button(label, key="lang_toggle", use_container_width=False,
                 help="Switch language · ভাষা বদলান"):
        i18n.toggle_lang()
        st.rerun()


def _theme_toggle() -> None:
    """One-tap theme switch: shows the active theme (☀️ light / 🌙 dark) and flips
    it on every click."""
    mode = C.get_mode()
    icon = "🌙" if mode == "dark" else "☀️"
    if st.button(icon, key="theme_toggle", use_container_width=False,
                 help=i18n.tf("Light ⇄ Dark theme", "লাইট ⇄ ডার্ক থিম")):
        db.set_meta("theme", "light" if mode == "dark" else "dark")
        st.rerun()


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
