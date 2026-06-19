"""
Localization for NutriSnap — English ⇄ Bangla.

Usage:
    from core.i18n import t
    st.button(t("Add food"))

`t(s)` returns the Bangla string for `s` when the language is set to "bn",
otherwise the original English. Unknown strings fall back to English, so nothing
ever breaks — you just see English until a translation is added to TRANSLATIONS.

The Bangla here is clean, standard Bangladeshi Bengali (প্রমিত বাংলা): polite
"আপনি/আপনার" with natural button phrasing ("যোগ করুন", "সেভ করুন", "দেখুন").

➜ When you add ANY new user-facing string elsewhere, wrap it in t() and add an
  entry here. See the [[bilingual-ui-maintenance]] note.
"""
from __future__ import annotations

import re

from core.i18n_foods import FOOD_NAMES

LANG_KEY = "lang"
LANGS = ("en", "bn")

# Western → Bengali numerals, and inline unit words.
_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
_UNIT_MAP = {"kcal": "ক্যালরি", "kg": "কেজি", "ml": "মিলি", "g": "গ্রাম"}
_UNIT_RE = re.compile(r"(\d[\d.,]*)\s*(kcal|kg|ml|g)\b")

# Serving-unit words (used in food "unit" strings like "1 bowl", "2 pieces").
_WORD_UNITS = {
    "serving": "পরিবেশন", "servings": "পরিবেশন", "bowl": "বাটি", "bowls": "বাটি",
    "plate": "প্লেট", "plates": "প্লেট", "piece": "পিস", "pieces": "পিস",
    "cup": "কাপ", "cups": "কাপ", "glass": "গ্লাস", "glasses": "গ্লাস",
    "slice": "স্লাইস", "slices": "স্লাইস", "medium": "মাঝারি", "large": "বড়",
    "small": "ছোট", "can": "ক্যান", "scoop": "স্কুপ", "scoops": "স্কুপ",
    "tbsp": "টেবিল চামচ", "tsp": "চা চামচ", "roll": "রোল", "bar": "বার",
    "burger": "বার্গার", "egg": "ডিম", "eggs": "ডিম",
}
_WORD_RE = re.compile(r"\b(" + "|".join(sorted(_WORD_UNITS, key=len, reverse=True)) + r")\b")


def get_lang() -> str:
    from core import database as db
    return db.get_meta(LANG_KEY, "en") or "en"


def set_lang(lang: str) -> None:
    from core import database as db
    db.set_meta(LANG_KEY, lang if lang in LANGS else "en")


def toggle_lang() -> str:
    new = "bn" if get_lang() == "en" else "en"
    set_lang(new)
    return new


def is_bn() -> bool:
    return get_lang() == "bn"


def num(x) -> str:
    """Western digits → Bengali digits (bn only)."""
    s = str(x)
    return s.translate(_DIGITS) if get_lang() == "bn" else s


def loc(s: str) -> str:
    """Localize a display string's numbers + units to Bangla (bn only).
    Safe for plain text — do NOT pass HTML/CSS (it would convert px/rgba digits)."""
    if not s or get_lang() != "bn":
        return s
    s = _UNIT_RE.sub(lambda m: m.group(1) + " " + _UNIT_MAP[m.group(2)], s)
    s = _WORD_RE.sub(lambda m: _WORD_UNITS[m.group(1).lower()], s)
    return s.translate(_DIGITS)


def t(s: str) -> str:
    """Translate a UI string or food name for the active language (English fallback)."""
    if not s or get_lang() != "bn":
        return s
    return _ALL.get(s, s)


def tf(en: str, bn: str) -> str:
    """Inline one-off translation; the Bangla side gets Bengali numerals + units."""
    return loc(bn) if get_lang() == "bn" else en


# --------------------------------------------------------------------------- #
#  English  →  Bangla (standard Bangladeshi Bengali)                          #
# --------------------------------------------------------------------------- #
TRANSLATIONS: dict[str, str] = {
    # ---- nav / chrome ----
    "Home": "হোম",
    "Diary": "ডায়েরি",
    "Scan": "স্ক্যান",
    "Coach": "কোচ",
    "More": "আরও",
    "AI Nutrition": "এআই নিউট্রিশন",
    "Everything else, one tap away.": "বাকি সবকিছু, এক ট্যাপ দূরে।",
    "Analytics": "অ্যানালিটিক্স",
    "Weight": "ওজন",
    "Hydration": "পানি",
    "Achievements": "অর্জন",
    "Settings": "সেটিংস",
    "Trends, macros, heatmap": "ট্রেন্ড, ম্যাক্রো, হিটম্যাপ",
    "Log & predict progress": "ওজন লিখুন ও অগ্রগতি দেখুন",
    "Track daily water": "প্রতিদিনের পানির হিসাব রাখুন",
    "Streaks, levels, badges": "স্ট্রিক, লেভেল, ব্যাজ",
    "Profile, goals, AI, data": "প্রোফাইল, লক্ষ্য, এআই, ডেটা",

    # ---- common buttons / words ----
    "Add food": "খাবার যোগ করুন",
    "Scan a meal": "খাবার স্ক্যান করুন",
    "Add": "যোগ করুন",
    "Save": "সেভ করুন",
    "Discard": "বাতিল করুন",
    "Continue  →": "এগিয়ে যান  →",
    "← Back": "← পেছনে",
    "Goal": "লক্ষ্য",
    "Food": "খাবার",
    "Left": "বাকি",
    "Current": "বর্তমান",
    "Start": "শুরু",
    "Change": "পরিবর্তন",
    "Target": "লক্ষ্য",
    "kcal": "ক্যালরি",
    "glasses": "গ্লাস",
    "protein": "প্রোটিন",
    "carbs": "কার্বস",
    "fat": "ফ্যাট",
    "fiber": "ফাইবার",
    "Protein": "প্রোটিন",
    "Carbs": "কার্বস",
    "Fat": "ফ্যাট",
    "Fiber": "ফাইবার",
    "Macros": "ম্যাক্রো",
    "Water": "পানি",

    # ---- greetings ----
    "Good morning": "শুভ সকাল",
    "Good afternoon": "শুভ দুপুর",
    "Good evening": "শুভ সন্ধ্যা",

    # ---- dashboard ----
    "💧 Water": "💧 পানি",
    "⚖️ Weight": "⚖️ ওজন",
    "Log weight": "ওজন লিখুন",
    "No weight logged yet": "এখনও কোনো ওজন লেখা হয়নি",
    "Target reached": "লক্ষ্যে পৌঁছেছেন",
    "Consistency (14 days):": "ধারাবাহিকতা (১৪ দিন):",
    "Max level 🎉": "সর্বোচ্চ লেভেল 🎉",
    "Nothing logged yet today. Scan or add a meal to see the breakdown.":
        "আজ এখনও কিছু লেখা হয়নি। স্ক্যান করুন বা খাবার যোগ করে হিসাব দেখুন।",
    "Open full diary  →": "পুরো ডায়েরি খুলুন  →",

    # ---- diary ----
    "Today": "আজ",
    "CONSUMED": "গৃহীত",
    "Nothing logged yet.": "এখনও কিছু লেখা হয়নি।",
    "All": "সব",
    "Bangladeshi": "বাংলাদেশি",
    "Fruit": "ফল",
    "Drinks": "পানীয়",
    "Sweets": "মিষ্টি",
    "Fast food": "ফাস্ট ফুড",
    "Everyday": "প্রতিদিনের",
    "🔍 Search": "🔍 খুঁজুন",
    "⭐ Favorites": "⭐ পছন্দের",
    "🕘 Recent": "🕘 সাম্প্রতিক",
    "🍱 Meals": "🍱 খাবার সেট",
    "✏️ Manual": "✏️ নিজে লিখুন",
    "Meal": "খাবারের বেলা",
    "Breakfast": "সকালের নাশতা",
    "Lunch": "দুপুরের খাবার",
    "Dinner": "রাতের খাবার",
    "Snacks": "হালকা নাশতা",
    "Cuisine": "রান্নার ধরন",
    "Search foods": "খাবার খুঁজুন",
    "Your most-logged foods will appear here.": "আপনার বেশি লেখা খাবারগুলো এখানে আসবে।",
    "Recently logged foods will appear here.": "সাম্প্রতিক লেখা খাবারগুলো এখানে আসবে।",
    "Create any food that isn't in the list. Optionally add a photo and save it to **My Foods** to reuse later.":
        "তালিকায় নেই এমন খাবার তৈরি করুন। চাইলে ছবি দিয়ে **আমার খাবার**-এ সেভ করে পরে আবার ব্যবহার করুন।",
    "Food name": "খাবারের নাম",
    "Emoji": "ইমোজি",
    "Serving (unit)": "পরিমাণ (একক)",
    "Qty": "সংখ্যা",
    "Photo (optional)": "ছবি (ঐচ্ছিক)",
    "Per serving · grams": "প্রতি পরিবেশন · গ্রাম",
    "⭐ Save to My Foods (reuse later)": "⭐ আমার খাবার-এ সেভ করুন (পরে ব্যবহার করুন)",
    "Add to diary": "ডায়েরিতে যোগ করুন",
    "My Foods": "আমার খাবার",

    # ---- scan ----
    "AI Food Scan": "এআই ফুড স্ক্যান",
    "Point, shoot, and let AI estimate the nutrition.":
        "ছবি তুলুন, এআই পুষ্টির হিসাব করে দেবে।",
    "● Live AI": "● লাইভ এআই",
    "● Demo mode": "● ডেমো মোড",
    "Cloud vision model connected": "ক্লাউড ভিশন মডেল যুক্ত আছে",
    "Add an Ollama key in Settings for real recognition":
        "আসল শনাক্তকরণের জন্য সেটিংসে একটি Ollama কী দিন",
    "📷 Camera": "📷 ক্যামেরা",
    "🖼️ Upload": "🖼️ আপলোড",
    "✨  Analyze with AI": "✨  এআই দিয়ে বিশ্লেষণ করুন",
    "No foods detected. Try a clearer, closer photo.":
        "কোনো খাবার পাওয়া যায়নি। আরেকটু কাছের, পরিষ্কার ছবি দিন।",
    "Detected foods": "শনাক্ত হওয়া খাবার",
    "Review and tweak — your edits are saved, not the guess.":
        "দেখে ঠিক করে নিন — আপনার সম্পাদনাটাই সেভ হবে, অনুমানটা নয়।",
    "Add to meal": "খাবারের বেলায় যোগ করুন",
    "💾  Save to diary": "💾  ডায়েরিতে সেভ করুন",
    "Include": "রাখুন",

    # ---- coach ----
    "AI Coach": "এআই কোচ",
    "Personalized advice from your real numbers.":
        "আপনার আসল হিসাব থেকে ব্যক্তিগত পরামর্শ।",
    "Connected": "যুক্ত আছে",
    "Offline": "অফলাইন",
    "Try asking": "জিজ্ঞেস করে দেখুন",
    "🗑 Clear conversation": "🗑 কথোপকথন মুছুন",
    "Ask your coach…": "কোচকে জিজ্ঞেস করুন…",
    "What should I eat for dinner?": "রাতে কী খাবো?",
    "How am I doing today?": "আজ আমি কেমন করছি?",
    "Give me a high-protein snack": "একটা বেশি-প্রোটিনের নাশতা বলুন",
    "Am I drinking enough water?": "আমি কি যথেষ্ট পানি খাচ্ছি?",

    # ---- weight ----
    "Track the trend, not the day-to-day noise.":
        "প্রতিদিনের ওঠানামা নয়, ট্রেন্ডটা দেখুন।",
    "Weight (kg)": "ওজন (কেজি)",
    "Date": "তারিখ",
    "💾  Log weight": "💾  ওজন লিখুন",
    "Log your first weight to start tracking the trend.":
        "ট্রেন্ড দেখা শুরু করতে আপনার প্রথম ওজনটা লিখুন।",
    "Weight over time": "সময়ের সাথে ওজন",
    "Your weigh-ins against your target": "আপনার লক্ষ্যের সাথে ওজনের তুলনা",
    "Progress to goal": "লক্ষ্যের দিকে অগ্রগতি",
    "Milestones": "মাইলফলক",
    "Every kilogram toward your goal": "লক্ষ্যের দিকে প্রতিটি কেজি",

    # ---- water ----
    "Small sips add up. Stay on top of your daily goal.":
        "একটু একটু করেই জমে। প্রতিদিনের লক্ষ্য ঠিক রাখুন।",
    "Goal reached — nicely hydrated today!": "লক্ষ্য পূরণ — আজ ভালো পানি খেয়েছেন!",
    "Quick add": "দ্রুত যোগ করুন",
    "Custom amount": "নিজের পরিমাণ",
    "↺ Reset today": "↺ আজকেরটা রিসেট করুন",
    "Last 7 days": "শেষ ৭ দিন",

    # ---- analytics ----
    "Spot trends across your week and month.":
        "সপ্তাহ ও মাসজুড়ে ট্রেন্ড দেখুন।",
    "7 days": "৭ দিন",
    "30 days": "৩০ দিন",
    "Avg / day": "গড় / দিন",
    "Days logged": "যেদিন লিখেছেন",
    "On-target days": "লক্ষ্যে থাকা দিন",
    "Best streak": "সেরা স্ট্রিক",
    "Calories vs goal": "ক্যালরি বনাম লক্ষ্য",
    "Average macro split": "গড় ম্যাক্রো ভাগ",
    "Share of calories from each macro": "প্রতিটি ম্যাক্রো থেকে ক্যালরির ভাগ",
    "Log some meals to see your macro breakdown.":
        "ম্যাক্রোর হিসাব দেখতে কিছু খাবার লিখুন।",
    "Protein intake": "প্রোটিন গ্রহণ",
    "Consistency · last 5 weeks": "ধারাবাহিকতা · শেষ ৫ সপ্তাহ",

    # ---- achievements ----
    "Build the habit, earn the badges.": "অভ্যাস গড়ুন, ব্যাজ জিতুন।",
    "Total XP": "মোট XP",
    "Current streak": "বর্তমান স্ট্রিক",
    "Consistency": "ধারাবাহিকতা",
    "Max level reached 🎉": "সর্বোচ্চ লেভেলে পৌঁছেছেন 🎉",

    # ---- settings ----
    "Profile, goals, AI and your data.": "প্রোফাইল, লক্ষ্য, এআই ও আপনার ডেটা।",
    "👤  Profile & goals": "👤  প্রোফাইল ও লক্ষ্য",
    "Name": "নাম",
    "Sex": "লিঙ্গ",
    "Male": "পুরুষ",
    "Female": "নারী",
    "Age": "বয়স",
    "Height (cm)": "উচ্চতা (সেমি)",
    "Activity": "কর্মক্ষমতা",
    "Save profile": "প্রোফাইল সেভ করুন",
    "Recalculate calorie & macro targets": "ক্যালরি ও ম্যাক্রো লক্ষ্য নতুন করে হিসাব করুন",
    "🎯  Daily targets": "🎯  প্রতিদিনের লক্ষ্য",
    "Save targets": "লক্ষ্য সেভ করুন",
    "🎨  Appearance": "🎨  চেহারা",
    "Theme": "থিম",
    "🤖  AI model (Ollama Cloud)": "🤖  এআই মডেল (Ollama ক্লাউড)",
    "Host": "হোস্ট",
    "API key": "এপিআই কী",
    "Save AI settings": "এআই সেটিংস সেভ করুন",
    "Test connection": "সংযোগ পরীক্ষা করুন",
    "🍽️  My foods": "🍽️  আমার খাবার",
    "🔒  Data & privacy": "🔒  ডেটা ও গোপনীয়তা",
    "Danger zone": "বিপদ অঞ্চল",
    "I understand this cannot be undone": "আমি বুঝেছি এটি আর ফেরানো যাবে না",
    "Clear all logs": "সব লগ মুছুন",
    "Reset everything": "সবকিছু রিসেট করুন",
    "📄  Privacy policy & terms": "📄  গোপনীয়তা নীতি ও শর্তাবলি",

    # ---- onboarding ----
    "AI nutrition tracking that feels effortless":
        "এমন এআই পুষ্টি হিসাব, যা একদম সহজ মনে হয়",
    "Welcome 👋": "স্বাগতম 👋",
    "Get started  →": "শুরু করুন  →",
    "About you": "আপনার সম্পর্কে",
    "We use this to calculate your calorie needs.":
        "এটি দিয়ে আপনার ক্যালরির প্রয়োজন হিসাব করি।",
    "Your goal": "আপনার লক্ষ্য",
    "Pick a goal and how active you are.":
        "একটি লক্ষ্য আর আপনি কতটা সক্রিয় তা বাছুন।",
    "Activity level": "কর্মক্ষমতার মাত্রা",
    "See my plan  →": "আমার প্ল্যান দেখুন  →",
    "Start tracking  🚀": "হিসাব শুরু করুন  🚀",
    "Target weight (kg)": "লক্ষ্য ওজন (কেজি)",
    "Weekly pace (kg/week)": "সাপ্তাহিক গতি (কেজি/সপ্তাহ)",

    # ---- gamification: levels ----
    "Sprout 🌱": "চারা 🌱",
    "Rookie 🥚": "নবিশ 🥚",
    "Tracker 🍃": "ট্র্যাকার 🍃",
    "Achiever 🌟": "অর্জনকারী 🌟",
    "Pro 💎": "প্রো 💎",
    "Elite 🔥": "এলিট 🔥",
    "Legend 👑": "কিংবদন্তি 👑",

    # ---- gamification: badges (name + description) ----
    "First Bite": "প্রথম কামড়",
    "Log your first food": "আপনার প্রথম খাবার লিখুন",
    "AI Vision": "এআই দৃষ্টি",
    "Scan a meal with the camera": "ক্যামেরা দিয়ে খাবার স্ক্যান করুন",
    "On the Scale": "দাঁড়িপাল্লায়",
    "Log your weight": "আপনার ওজন লিখুন",
    "Hydrated": "পানিতে পূর্ণ",
    "Hit your daily water goal": "প্রতিদিনের পানির লক্ষ্য পূরণ করুন",
    "On Target": "লক্ষ্যে",
    "Land within 100 kcal of your goal": "লক্ষ্যের ১০০ ক্যালরির মধ্যে থাকুন",
    "Protein Pro": "প্রোটিন প্রো",
    "Reach your daily protein goal": "প্রতিদিনের প্রোটিন লক্ষ্য পূরণ করুন",
    "Warming Up": "শুরু হচ্ছে",
    "3-day logging streak": "৩ দিনের স্ট্রিক",
    "Week Warrior": "সপ্তাহ যোদ্ধা",
    "7-day logging streak": "৭ দিনের স্ট্রিক",
    "Unstoppable": "অপ্রতিরোধ্য",
    "30-day logging streak": "৩০ দিনের স্ট্রিক",
    "Balanced Day": "ভারসাম্যের দিন",
    "Hit all 3 macro goals in a day": "এক দিনে ৩টি ম্যাক্রো লক্ষ্যই পূরণ করুন",
    "Explorer": "অভিযাত্রী",
    "Log 20 different foods": "২০টি ভিন্ন খাবার লিখুন",
    "Centurion": "শতবীর",
    "Log 100 foods total": "মোট ১০০টি খাবার লিখুন",

    # ---- goals (display only — code keeps the English keys) ----
    "Lose weight": "ওজন কমানো",
    "Maintain": "ধরে রাখা",
    "Gain weight": "ওজন বাড়ানো",
    "Build muscle": "পেশি গঠন",

    # ---- activity levels (display only) ----
    "Sedentary": "নিষ্ক্রিয়",
    "Lightly active": "হালকা সক্রিয়",
    "Moderately active": "মাঝারি সক্রিয়",
    "Very active": "খুব সক্রিয়",
    "Athlete": "ক্রীড়াবিদ",
    "Little or no exercise": "অল্প বা কোনো ব্যায়াম নয়",
    "Light exercise 1–3 days/wk": "হালকা ব্যায়াম, সপ্তাহে ১–৩ দিন",
    "Moderate exercise 3–5 days/wk": "মাঝারি ব্যায়াম, সপ্তাহে ৩–৫ দিন",
    "Hard exercise 6–7 days/wk": "কঠিন ব্যায়াম, সপ্তাহে ৬–৭ দিন",
    "Training twice a day": "দিনে দুইবার অনুশীলন",
}

# Combined lookup: UI strings take priority, then food names.
_ALL: dict[str, str] = {**FOOD_NAMES, **TRANSLATIONS}
