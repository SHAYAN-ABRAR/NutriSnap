# 🥗 NutriSnap — AI-Powered Calorie & Nutrition Tracker

A premium, **mobile-first**, **local-first** calorie tracker built with Python + Streamlit.
Snap a photo of your meal, let AI estimate the calories and macros, and track your weight,
water and habits — all stored privately on your device, no account required.

Designed to feel like a commercial fitness product (think MyFitnessPal × Apple Health),
and deployable to **Streamlit Community Cloud straight from GitHub** in a couple of clicks.

![NutriSnap](https://img.shields.io/badge/Streamlit-ready-FF4B4B?logo=streamlit) ![Local-first](https://img.shields.io/badge/data-100%25%20local-00e5a0) ![No auth](https://img.shields.io/badge/auth-none-success)

---

## ✨ Features

| Area | What you get |
|------|--------------|
| 📸 **AI Food Scan** | Camera capture or upload → detected foods, calories, protein/carbs/fat/fiber, portion & confidence score. Editable before saving. |
| 🏠 **Dashboard** | Animated calorie ring, macro bars, water & weight cards, level/XP, streak. |
| 📒 **Food Diary** | Breakfast/Lunch/Dinner/Snacks. Add via search, favorites, recents, AI photo, or manual entry. Quantity steppers (−/+), day navigator. |
| 🇧🇩 **Food catalog** | **200+ foods** with a heavy focus on **Bangladeshi cuisine** — dishes (biryani, ilish, bhorta, pithas, sweets, street food…), local fruits (aam, kathal, peyara…) and global savory items (burger, shawarma, sandwich…), all with real photos + a cuisine filter. |
| 🌐 **Bilingual** | One-tap **English ⇄ বাংলা** toggle. Every label, food name, number (০১২৩…) and unit (ক্যালরি/কেজি/মিলি/গ্রাম) localizes into clean standard Bangladeshi Bengali. |
| 📊 **Analytics** | 7/30-day calorie trends, macro split donut, protein trend, 5-week consistency heatmap. |
| ⚖️ **Weight** | Logging, trend chart with target line, goal-date prediction, milestones. |
| 💧 **Hydration** | One-tap & custom water logging, daily ring, weekly history. |
| 🤖 **AI Coach** | Chat assistant grounded in *your* live stats (works offline too). |
| 🏆 **Gamification** | 12 achievements, streaks, levels/XP, consistency score, celebrations. |
| ⚙️ **Settings** | Profile & goals, manual targets, dark/light theme, AI connection, data export, privacy & legal. |
| 🚀 **Onboarding** | 4-step flow that computes personalized calorie/macro targets (Mifflin–St Jeor). |

**Accessibility:** WCAG-minded contrast, large touch targets, keyboard-navigable controls, `prefers-reduced-motion` support, light & dark themes.

---

## 🧠 AI: how it works

NutriSnap uses an **[Ollama](https://ollama.com) Cloud** (or self-hosted) vision/chat model.

- **With a key** → real photo recognition + full conversational coaching.
- **Without a key (default)** → a built-in **offline demo**: an on-device colour heuristic estimates the meal, and the coach answers from your real numbers. Nothing feels broken on first run.

Add your key in **Settings → AI model**. It's stored only in your local database.

---

## 🚀 Run locally

```bash
# 1. clone
git clone https://github.com/SHAYAN-ABRAR/NutriSnap.git
cd NutriSnap

# 2. (optional) virtual env
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. install + run
pip install -r requirements.txt
streamlit run app.py
# If "streamlit" isn't found on PATH, use the module form (always works):
python -m streamlit run app.py
```

Open http://localhost:8501 — best viewed in a narrow / mobile window (or your browser's device toolbar).

---


## 🗂️ Project structure

```
nutrisnap/
├── app.py                  # router, header, mobile nav, onboarding gate
├── requirements.txt
├── .streamlit/config.toml  # theme + server config
├── core/
│   ├── theme.py            # design system + light/dark CSS
│   ├── database.py         # SQLite local storage (all CRUD)
│   ├── nutrition.py        # BMR/TDEE, goals, macros, food database
│   ├── foods_bd.py *_extra # generated catalogs: BD dishes + fruits + global foods (with image URLs)
│   ├── i18n.py             # English ⇄ Bangla engine (t / tf / loc / num)
│   ├── i18n_foods.py       # food-name translations (English → বাংলা)
│   ├── ai.py               # Ollama cloud vision + chat (+ offline fallback)
│   ├── gamification.py     # streaks, achievements, levels/XP
│   ├── components.py       # rings, charts, cards, celebrations
│   └── state.py            # session helpers + daily-context builder
└── views/
    ├── onboarding.py  dashboard.py  diary.py  scan.py  analytics.py
    └── weight.py  water.py  coach.py  achievements.py  settings.py
```

---

## 🏛️ Architecture at a glance

```
┌──────────────┐    ┌────────────────────────────┐    ┌──────────────────┐
│  Streamlit   │───▶│  views/  (one screen each) │───▶│  core/ engines   │
│  UI (mobile) │    │  render(palette)           │    │  nutrition / ai  │
└──────────────┘    └────────────────────────────┘    │  gamification    │
        ▲                        │                     └────────┬─────────┘
        │  CSS design system     ▼                              │
        └────────────  core/theme.py        core/database.py (SQLite) ◀──┘
                                             core/ai.py ─▶ Ollama Cloud API
```

- **Local-first:** every read/write goes through `core/database.py` → one SQLite file.
- **Stateless views:** each `render()` recomputes from the DB + `state.daily_context()`.
- **Pluggable AI:** `core/ai.py` is the only network boundary; swap the provider in one place.

---

## 📈 Scaling & next steps

- **Persistent storage:** point `DB_PATH` at a mounted volume, or replace SQLite with Postgres/Supabase for multi-device sync.
- **Auth (if ever needed):** add Streamlit native auth or a thin login; keep the local mode as the default.
- **Provider swap:** `core/ai.py` can target any OpenAI-compatible / Ollama endpoint.
- **Verified food DB:** wire `core/nutrition.search_foods` to USDA FoodData Central or Open Food Facts.
- **Regenerate the catalog:** edit the `CATALOG` list in `_build_bd.py` and run `python _build_bd.py` to refetch Wikimedia thumbnails into `core/foods_bd.py`. (Photos hotlink Wikimedia and need a network connection at display time; items without a Wikipedia image fall back to an emoji.)
- **PWA / native feel:** wrap with a PWA manifest or ship via a WebView shell.

---

## 🔒 Privacy & disclaimer

Data is stored locally; nothing is transmitted except photos/messages you choose to send to your configured AI model. NutriSnap provides **estimates for general wellness only — not medical advice**. AI photo estimates are approximations; verify important values. Consult a professional before significant dietary changes.

---

Built with ❤️ using Streamlit, Plotly & Ollama. MIT-style use — adapt freely.
