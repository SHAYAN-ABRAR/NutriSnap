"""Food diary: meals by section, search/add, favorites, recents, manual entry."""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st
from st_keyup import st_keyup

from core import database as db
from core import nutrition as N
from core import components as C
from core import state as S
from core import i18n
from core.i18n import t, loc, num

MEALS = [("Breakfast", "🌅"), ("Lunch", "🌞"), ("Dinner", "🌙"), ("Snacks", "🍪")]


def render(p: dict) -> None:
    ss = st.session_state
    ss.setdefault("diary_date", date.today().isoformat())
    C.ramadan_banner()   # #11

    # ---- date navigator ----
    cur = date.fromisoformat(ss.diary_date)
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    if nav1.button("‹", use_container_width=True, key="d_prev"):
        ss.diary_date = (cur - timedelta(days=1)).isoformat(); st.rerun()
    label = t("Today") if cur == date.today() else cur.strftime("%a, %d %b")
    nav2.markdown(f"<div style='text-align:center;font-family:Space Grotesk;font-weight:700;font-size:1.1rem;padding-top:8px'>{label}</div>",
                  unsafe_allow_html=True)
    is_today = cur == date.today()
    if nav3.button("›", use_container_width=True, key="d_next", disabled=is_today):
        ss.diary_date = (cur + timedelta(days=1)).isoformat(); st.rerun()

    d = ss.diary_date
    totals = db.day_totals(d)
    prof = db.get_profile() or {}
    goal = prof.get("calorie_goal", 2000)
    of_lbl = i18n.tf(f"of {goal} kcal", f"{goal} ক্যালরির মধ্যে")
    left_lbl = i18n.tf(f"{int(max(0, goal - totals['calories']))} left",
                       f"{int(max(0, goal - totals['calories']))} বাকি")
    C.html(
        "<div class='ns-card' style='display:flex;justify-content:space-between;align-items:center'>"
        f"<div><div class='ns-sub'>{t('CONSUMED')}</div><div class='ns-big'>{int(totals['calories'])}</div></div>"
        f"<div style='text-align:right'><div class='ns-sub'>{of_lbl}</div>"
        f"<div class='ns-h' style='color:var(--accent)'>{left_lbl}</div></div></div>"
    )

    # ---- empty state (#5) when the whole day is blank ----
    if totals["items"] == 0:
        C.html(f"<div class='ns-empty' style='margin-bottom:12px'><span class='emoji'>🍽️</span>"
               f"<b>{i18n.tf('No meals logged yet', 'এখনও কোনো খাবার লেখা হয়নি')}</b><br>"
               f"{i18n.tf('Search, scan a photo, or add a custom food below.', 'নিচে খুঁজুন, ছবি তুলুন বা নিজের খাবার যোগ করুন।')}</div>")

    # ---- add food panel ----
    with st.expander(f"➕  {t('Add food')}", expanded=totals["items"] == 0):
        _add_panel(d)

    # ---- meals ----
    meal_list = S.meals()
    by_meal: dict[str, list] = {m: [] for m, _ in meal_list}
    for f in db.get_foods(d):
        by_meal.setdefault(f["meal"], []).append(f)
    # include any logged meals not in the current set (so toggling Ramadan mode
    # never hides previously-logged data)
    extra = [(m, "🍽️") for m in by_meal if m not in dict(meal_list) and by_meal[m]]

    for meal, emoji in meal_list + extra:
        items = by_meal.get(meal, [])
        cals = sum(i["calories"] * i["qty"] for i in items)
        with C.card():
            C.html(f"<div style='display:flex;justify-content:space-between'>"
                   f"<div class='ns-h'>{emoji} {t(meal)}</div>"
                   f"<div class='ns-sub'>{loc(f'{int(cals)} kcal')}</div></div>")
            if not items:
                C.html(f"<div class='ns-sub' style='padding:8px 0'>{t('Nothing logged yet.')}</div>")
            for it in items:
                qty = it["qty"] or 1
                tc, tp, tcb, tf = (it["calories"] * qty, it["protein"] * qty,
                                   it["carbs"] * qty, it["fat"] * qty)
                fc1, dec, num, inc, dele = st.columns([4, 1, 0.8, 1, 1])
                fc1.markdown(
                    f"<div class='ns-food'><div style='display:flex;align-items:center'>"
                    f"{C.food_icon(it, 34)}<div>"
                    f"<b>{t(it['name'])}</b> <span class='ns-sub'>· {loc(it['unit'])}</span><br>"
                    f"<span class='ns-sub'>{loc(f'{int(tc)} kcal')} · "
                    f"{loc(f'{int(tp)}g')} {t('protein')} · {loc(f'{int(tcb)}g')} {t('carbs')} · {loc(f'{int(tf)}g')} {t('fat')}</span></div></div></div>",
                    unsafe_allow_html=True,
                )
                if dec.button("−", key=f"dec{it['id']}", use_container_width=True,
                              help="Decrease quantity"):
                    db.adjust_food_qty(it["id"], -1); st.rerun()
                num.markdown(
                    f"<div class='ns-qty'>{qty:g}</div>", unsafe_allow_html=True)
                if inc.button("+", key=f"inc{it['id']}", use_container_width=True,
                              help="Increase quantity"):
                    db.adjust_food_qty(it["id"], +1); st.rerun()
                if dele.button("🗑", key=f"del{it['id']}", use_container_width=True,
                               help="Remove"):
                    db.delete_food(it["id"]); st.rerun()

    S.run_achievement_check()


def _add_panel(log_date: str):
    ss = st.session_state
    open_food = _build_food_dialog(log_date)   # #2 food-detail dialog
    src = st.radio("Source", ["🔍 Search", "⭐ Favorites", "🕘 Recent", "🍱 Meals", "✏️ Manual"],
                   horizontal=True, label_visibility="collapsed", key="add_src", format_func=t)
    meal = st.selectbox(t("Meal"), [m for m, _ in S.meals()], key="add_meal", format_func=t)

    if src == "🔍 Search":
        # apply a recent-search chip queued on the previous run (set BEFORE the widget)
        if "pending_search" in ss:
            ss["add_q"] = ss.pop("pending_search")
        cat = st.segmented_control("Cuisine", N.categories(), default=None,
                                   key="add_cat", label_visibility="collapsed", format_func=t) or "All"
        # st_keyup reruns on each keystroke (debounced) so results update live
        q = st_keyup(t("Search foods"),
                     placeholder=i18n.tf("e.g. biryani, mango, burger, ilish…",
                                         "যেমন বিরিয়ানি, আম, বার্গার, ইলিশ…"),
                     key="add_q", debounce=200) or ""
        # recent searches (#9) — quick chips when the box is empty
        if not q.strip():
            recents = db.get_recent_searches()
            if recents:
                C.html(f"<div class='ns-sub' style='margin:4px 2px 2px'>"
                       f"{i18n.tf('Recent searches', 'সাম্প্রতিক খোঁজা')}</div>")
                rcols = st.columns(3)
                for i, term in enumerate(recents[:6]):
                    if rcols[i % 3].button(f"🔎 {term}", key=f"rs{i}", use_container_width=True):
                        ss["pending_search"] = term
                        st.rerun()
        # show more when browsing a whole cuisine without a query
        limit = 14 if q.strip() else (40 if cat != "All" else 14)
        results = N.search_foods(q, limit=limit, category=cat)
        if not results and q.strip():
            st.caption(i18n.tf(f"No matches for “{q}”.", f"“{q}” এর কোনো মিল পাওয়া যায়নি।"))
            if st.button(i18n.tf(f"➕  Create “{q}” as a custom food",
                                 f"➕  “{q}” একটি নিজের খাবার হিসেবে তৈরি করুন"),
                         use_container_width=True, key="create_from_search"):
                ss["prefill_name"] = q
                ss["add_src"] = "✏️ Manual"
                st.rerun()
        for i, f in enumerate(results):
            _food_button(f, meal, log_date, f"srch{i}", open_food=open_food, query=q)

    elif src == "⭐ Favorites":
        favs = db.favorites()
        if not favs:
            st.caption(t("Your most-logged foods will appear here."))
        for i, f in enumerate(favs):
            _food_button(f, meal, log_date, f"fav{i}", open_food=open_food,
                         subtitle=i18n.tf(f"logged {f['freq']}×", f"{f['freq']}× লেখা হয়েছে"))

    elif src == "🕘 Recent":
        recents = db.recent_foods()
        if not recents:
            st.caption(t("Recently logged foods will appear here."))
        for i, f in enumerate(recents):
            _food_button(f, meal, log_date, f"rec{i}", open_food=open_food)

    elif src == "🍱 Meals":
        _meal_templates_panel(meal, log_date)

    else:  # Manual — create your own food
        st.caption(t("Create any food that isn't in the list. Optionally add a photo and "
                     "save it to **My Foods** to reuse later."))
        with st.form("manual_food", clear_on_submit=True):
            name = st.text_input(t("Food name"), value=ss.pop("prefill_name", ""),
                                 placeholder=i18n.tf("e.g. Grandma's beef tehari",
                                                     "যেমন দাদির গরুর তেহারি"))
            c1, c2, c3 = st.columns([1, 2, 1])
            emoji = c1.text_input(t("Emoji"), value="🍽️", max_chars=2)
            unit = c2.text_input(t("Serving (unit)"), value="1 serving",
                                 placeholder=i18n.tf("e.g. 1 plate, 250 g", "যেমন ১ প্লেট, ২৫০ গ্রাম"))
            qty = c3.number_input(t("Qty"), 0.25, 20.0, 1.0, 0.25)
            photo = st.file_uploader(t("Photo (optional)"), type=["jpg", "jpeg", "png", "webp"])
            st.caption(t("Per serving · grams"))
            m1, m2, m3, m4, m5 = st.columns(5)
            cal = m1.number_input(t("kcal"), 0, 4000, 250, help="Calories")
            pro = m2.number_input(t("Protein"), 0, 400, 10, help="Protein (g)")
            car = m3.number_input(t("Carbs"), 0, 600, 30, help="Carbohydrates (g)")
            fat = m4.number_input(t("Fat"), 0, 300, 8, help="Fat (g)")
            fib = m5.number_input(t("Fiber"), 0, 150, 3, help="Fiber (g)")
            save_lib = st.checkbox(t("⭐ Save to My Foods (reuse later)"), value=True)
            if st.form_submit_button(t("Add to diary"), type="primary", use_container_width=True):
                image = C.image_to_datauri(photo) if photo else ""
                item = {"name": name or "Custom food", "emoji": emoji or "🍽️", "image": image,
                        "unit": unit or "1 serving", "calories": cal, "protein": pro,
                        "carbs": car, "fat": fat, "fiber": fib}
                if save_lib:
                    db.add_custom_food(item)
                db.add_food(meal, {**item, "qty": qty, "source": "custom"}, log_date)
                S.run_achievement_check()
                st.toast(i18n.tf(f"Added {name or 'food'} ✓", f"{name or 'খাবার'} যোগ হয়েছে ✓")
                         + (i18n.tf("  ·  saved to My Foods", "  ·  আমার খাবার-এ সেভ হয়েছে") if save_lib else ""),
                         icon="✅")
                st.rerun()


def _food_button(f: dict, meal: str, log_date: str, key: str, subtitle: str = "",
                 open_food=None, query: str = ""):
    c1, c2, c3 = st.columns([5, 1, 1.6])
    sub = subtitle or f.get("unit", "1 serving")
    cat = f.get("cat")
    tag = f" <span class='ns-sub'>· {t(cat)}</span>" if cat and cat not in ("Everyday", None) else ""
    cals = loc(f"{int(f['calories'])} kcal")
    c1.markdown(
        f"<div style='padding-top:4px;display:flex;align-items:center'>{C.food_icon(f, 38)}"
        f"<div><b>{t(f['name'])}</b>{tag}<br>"
        f"<span class='ns-sub'>{cals} · {loc(sub)}</span></div></div>",
        unsafe_allow_html=True,
    )
    # ℹ️ opens the detail sheet (#2) with portion presets (#10)
    if open_food and c2.button("ℹ️", key=f"{key}_i", use_container_width=True,
                               help=i18n.tf("Details & portion", "বিবরণ ও পরিমাণ")):
        if query:
            db.add_recent_search(query)
        st.session_state["detail_qty"] = 1.0
        open_food(f, meal)
    if c3.button(t("Add"), key=key, use_container_width=True):
        db.add_food(meal, {**f, "qty": 1, "unit": f.get("unit", "serving"),
                           "image": f.get("image", ""), "source": "library"}, log_date)
        if query:
            db.add_recent_search(query)
        S.run_achievement_check()
        st.toast(i18n.tf(f"Added {f['name']} to {meal} ✓", f"{t(f['name'])} {t(meal)}-এ যোগ হয়েছে ✓"), icon="✅")
        st.rerun()


# ----------------------- food detail sheet (#2) + presets (#10) --------------
def _build_food_dialog(log_date: str):
    """Return a localized @st.dialog showing a food's macros, portion presets and Add."""
    @st.dialog(i18n.tf("Food details", "খাবারের বিবরণ"))
    def _dlg(f: dict, meal: str):
        _food_detail_body(f, meal, log_date)
    return _dlg


def _food_detail_body(f: dict, meal: str, log_date: str) -> None:
    ss = st.session_state
    cals = f.get("calories", 0)
    C.html(
        f"<div style='display:flex;align-items:center;gap:4px'>{C.food_icon(f, 52)}"
        f"<div><div class='ns-h'>{t(f['name'])}</div>"
        f"<div class='ns-sub'>{loc(f.get('unit', '1 serving'))}</div></div></div>"
    )
    pro, car = int(f.get("protein", 0)), int(f.get("carbs", 0))
    fat, fib = int(f.get("fat", 0)), int(f.get("fiber", 0))
    C.html(
        f"<div class='ns-sub' style='margin:8px 0 4px'>"
        f"{loc(f'{int(cals)} kcal')} · {loc(f'{pro}g')} {t('protein')} · "
        f"{loc(f'{car}g')} {t('carbs')} · {loc(f'{fat}g')} {t('fat')} · "
        f"{loc(f'{fib}g')} {t('fiber')}</div>"
    )

    C.html(f"<div class='ns-sub' style='margin:6px 2px 2px'>{i18n.tf('Portion', 'পরিমাণ')}</div>")
    ss.setdefault("detail_qty", 1.0)
    pc = st.columns([1, 1, 1, 2])
    for i, (lbl, val) in enumerate([("½", 0.5), ("1", 1.0), ("2", 2.0)]):
        if pc[i].button(lbl, key=f"pp_{i}", use_container_width=True):
            ss["detail_qty"] = float(val)
            st.rerun()
    qty = pc[3].number_input(i18n.tf("Qty", "সংখ্যা"), 0.25, 30.0, step=0.25,
                             key="detail_qty", label_visibility="collapsed")

    total = int(cals * qty)
    C.html(f"<div class='ns-card' style='text-align:center;margin:8px 0'>"
           f"<span class='ns-sub'>{i18n.tf('Total to add', 'যোগ করার মোট')}</span> "
           f"<b class='ns-grad' style='font-size:1.2rem'>{loc(f'{total} kcal')}</b></div>")

    if st.button(i18n.tf(f"➕  Add to {t(meal)}", f"➕  {t(meal)}-এ যোগ করুন"),
                 type="primary", use_container_width=True, key="detail_add"):
        db.add_food(meal, {**f, "qty": float(qty), "unit": f.get("unit", "serving"),
                           "image": f.get("image", ""), "source": "library"}, log_date)
        S.run_achievement_check()
        ss.pop("detail_qty", None)
        st.toast(i18n.tf(f"Added {f['name']} to {meal} ✓",
                         f"{t(f['name'])} {t(meal)}-এ যোগ হয়েছে ✓"), icon="✅")
        st.rerun()


# --------------------------- meal templates (#1) -----------------------------
def _meal_templates_panel(meal: str, log_date: str) -> None:
    tpls = db.get_meal_templates()
    if not tpls:
        st.caption(i18n.tf("Save a meal you eat often, then log the whole thing in one tap.",
                           "প্রায়ই খান এমন একটা খাবার সেট সেভ করুন, পরে এক ট্যাপে পুরোটা যোগ করুন।"))
    for i, tpl in enumerate(tpls):
        items = tpl.get("items", [])
        tot = int(sum(it.get("calories", 0) * it.get("qty", 1) for it in items))
        meta = i18n.tf(f"{len(items)} items · {tot} kcal", f"{len(items)}টি · {tot} ক্যালরি")
        c1, c2, c3 = st.columns([5, 1.5, 1])
        c1.markdown(
            f"<div style='padding-top:4px'><b>🍱 {tpl['name']}</b><br>"
            f"<span class='ns-sub'>{loc(meta)}</span></div>", unsafe_allow_html=True)
        if c2.button(t("Add"), key=f"tpl{i}", use_container_width=True):
            for it in items:
                db.add_food(meal, {**it, "qty": it.get("qty", 1), "source": "template"}, log_date)
            S.run_achievement_check()
            st.toast(i18n.tf(f"Added “{tpl['name']}” to {meal} ✓",
                             f"“{tpl['name']}” {t(meal)}-এ যোগ হয়েছে ✓"), icon="✅")
            st.rerun()
        if c3.button("🗑", key=f"tpldel{i}", use_container_width=True):
            db.delete_meal_template(tpl["name"])
            st.rerun()

    st.divider()
    cur = [f for f in db.get_foods(log_date) if f["meal"] == meal]
    if cur:
        with st.form("save_tpl", clear_on_submit=True):
            nm = st.text_input(i18n.tf("Template name", "টেমপ্লেটের নাম"),
                               placeholder=i18n.tf(f"e.g. My {meal}", f"যেমন আমার {t(meal)}"))
            if st.form_submit_button(
                    i18n.tf(f"💾  Save current {t(meal)} ({len(cur)} items)",
                            f"💾  বর্তমান {t(meal)} সেভ করুন ({len(cur)}টি)"),
                    type="primary", use_container_width=True):
                keys = ("name", "emoji", "image", "unit", "calories", "protein",
                        "carbs", "fat", "fiber", "qty")
                items = [{k: it.get(k) for k in keys} for it in cur]
                db.save_meal_template(nm or t(meal), items)
                st.toast(i18n.tf("Meal template saved ✓", "খাবার সেট সেভ হয়েছে ✓"), icon="✅")
                st.rerun()
    else:
        st.caption(i18n.tf(f"Add foods to {meal} today first, then save them as a reusable template.",
                           f"আগে আজকের {t(meal)}-এ খাবার যোগ করুন, তারপর টেমপ্লেট হিসেবে সেভ করুন।"))
