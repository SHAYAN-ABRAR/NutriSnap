"""
AI layer — food-photo recognition and the nutrition coach.

Primary path: an Ollama cloud (or self-hosted) vision/chat model.
Fallback path: a fully offline heuristic so the product works with zero config
(important for demos / first run). The fallback inspects real image colour to
make a believable estimate and the coach answers from the user's actual data.
"""
from __future__ import annotations

import io
import json
import base64
import hashlib
import random
import re

import requests

from core import nutrition

DEFAULT_HOST = "https://ollama.com"          # Ollama Cloud
DEFAULT_VISION_MODEL = "gemma3:27b"          # multimodal, cloud-available
DEFAULT_CHAT_MODEL = "gemma3:27b"
TIMEOUT = 90


# ------------------------------- configuration -------------------------------
def get_config() -> dict:
    """Read AI settings from the local DB (lazy import to avoid cycles)."""
    from core import database as db
    cfg = db.get_meta("ai_config", {}) or {}
    return {
        "host": cfg.get("host", DEFAULT_HOST),
        "api_key": cfg.get("api_key", ""),
        "vision_model": cfg.get("vision_model", DEFAULT_VISION_MODEL),
        "chat_model": cfg.get("chat_model", DEFAULT_CHAT_MODEL),
        "enabled": bool(cfg.get("api_key")),
    }


def is_live() -> bool:
    return get_config()["enabled"]


def _chat(messages, model, cfg, want_json=False) -> str:
    headers = {"Content-Type": "application/json"}
    if cfg["api_key"]:
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    payload = {"model": model, "messages": messages, "stream": False}
    if want_json:
        payload["format"] = "json"
    r = requests.post(f"{cfg['host'].rstrip('/')}/api/chat",
                      headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data.get("message", {}).get("content", "")


# ----------------------------- food recognition ------------------------------
VISION_PROMPT = (
    "You are a nutrition vision model. Identify every distinct food/drink in this "
    "image. Respond ONLY with JSON of the form: "
    '{"foods":[{"name":"","emoji":"","portion":"","calories":0,"protein":0,'
    '"carbs":0,"fat":0,"fiber":0,"confidence":0.0}]} '
    "Estimate per the visible portion. confidence is 0-1. Use one emoji per food."
)


def analyze_food(image_bytes: bytes) -> dict:
    """Return {'foods': [...], 'live': bool, 'note': str}."""
    cfg = get_config()
    if cfg["enabled"]:
        try:
            b64 = base64.b64encode(image_bytes).decode()
            content = _chat(
                [{"role": "user", "content": VISION_PROMPT, "images": [b64]}],
                cfg["vision_model"], cfg, want_json=True,
            )
            foods = _parse_foods(content)
            if foods:
                return {"foods": foods, "live": True,
                        "note": f"Analyzed by {cfg['vision_model']}"}
        except Exception as e:  # network / model / parse — fall through to heuristic
            return {"foods": _heuristic(image_bytes), "live": False,
                    "note": f"Cloud model unavailable ({type(e).__name__}). Showing on-device estimate."}
    return {"foods": _heuristic(image_bytes), "live": False,
            "note": "Demo mode (no AI key) — on-device colour estimate. Add a key in Settings for real recognition."}


def _parse_foods(text: str) -> list[dict]:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    raw = data.get("foods", data if isinstance(data, list) else [])
    out = []
    for f in raw:
        out.append({
            "name": str(f.get("name", "Food")).title(),
            "emoji": f.get("emoji") or "🍽️",
            "unit": f.get("portion") or "1 serving",
            "qty": 1.0,
            "calories": _num(f.get("calories")),
            "protein": _num(f.get("protein")),
            "carbs": _num(f.get("carbs")),
            "fat": _num(f.get("fat")),
            "fiber": _num(f.get("fiber")),
            "confidence": float(f.get("confidence", 0.8) or 0.8),
            "source": "ai_vision",
        })
    return out


def _num(v) -> float:
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return 0.0


def _avg_color(image_bytes: bytes):
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((32, 32))
        px = list(img.getdata())
        n = len(px)
        r = sum(p[0] for p in px) / n
        g = sum(p[1] for p in px) / n
        b = sum(p[2] for p in px) / n
        return r, g, b
    except Exception:
        return 150, 150, 150


# food families biased by dominant colour, for the offline estimate
_FAMILIES = {
    "green":  ["Mixed Green Salad", "Caesar Salad", "Tofu Bowl", "Avocado Toast"],
    "red":    ["Margherita Pizza", "Cheeseburger", "Beef Steak", "Spaghetti Bolognese"],
    "yellow": ["Pancakes", "French Fries", "Croissant", "Brown Rice"],
    "white":  ["Greek Yogurt", "Brown Rice", "Sushi Roll", "Cottage Cheese"],
    "brown":  ["Grilled Chicken Breast", "Chicken Stir-fry", "Lentil Soup", "Beef Steak"],
}


def _heuristic(image_bytes: bytes) -> list[dict]:
    r, g, b = _avg_color(image_bytes)
    if g > r and g > b:
        fam = "green"
    elif r > 150 and g < 120 and b < 120:
        fam = "red"
    elif r > 170 and g > 150 and b < 130:
        fam = "yellow"
    elif r > 180 and g > 180 and b > 180:
        fam = "white"
    else:
        fam = "brown"

    seed = int(hashlib.md5(image_bytes[:4096]).hexdigest(), 16) % (10 ** 8)
    rng = random.Random(seed)
    names = _FAMILIES[fam]
    k = rng.choice([1, 1, 2])
    chosen = rng.sample(names, k=min(k, len(names)))
    out = []
    for name in chosen:
        base = nutrition.find_food(name) or {}
        scale = rng.uniform(0.85, 1.2)
        out.append({
            "name": name, "emoji": base.get("emoji", "🍽️"),
            "unit": base.get("unit", "1 serving"), "qty": 1.0,
            "calories": round(base.get("calories", 250) * scale),
            "protein": round(base.get("protein", 12) * scale, 1),
            "carbs": round(base.get("carbs", 25) * scale, 1),
            "fat": round(base.get("fat", 10) * scale, 1),
            "fiber": round(base.get("fiber", 3) * scale, 1),
            "confidence": round(rng.uniform(0.62, 0.79), 2),
            "source": "ai_demo",
        })
    return out


# ------------------------------- nutrition coach -----------------------------
COACH_SYSTEM = (
    "You are NutriSnap Coach, a warm, concise, evidence-based nutrition assistant. "
    "Give practical, encouraging, non-judgmental advice in 2–5 short sentences. "
    "Use the user's live stats when relevant. Never give medical diagnoses; suggest "
    "a professional for medical concerns."
)


def coach_reply(message: str, context: dict, history: list[dict]) -> str:
    cfg = get_config()
    if cfg["enabled"]:
        try:
            ctx = _context_blurb(context)
            msgs = [{"role": "system", "content": COACH_SYSTEM + "\n\nUser stats:\n" + ctx}]
            for h in history[-8:]:
                msgs.append({"role": h["role"], "content": h["content"]})
            msgs.append({"role": "user", "content": message})
            reply = _chat(msgs, cfg["chat_model"], cfg)
            if reply.strip():
                return reply.strip()
        except Exception:
            pass
    return _coach_fallback(message, context)


def _context_blurb(c: dict) -> str:
    return (
        f"- Goal: {c.get('goal')}\n"
        f"- Daily calorie target: {c.get('calorie_goal')} kcal\n"
        f"- Eaten today: {round(c.get('consumed', 0))} kcal "
        f"({round(c.get('remaining', 0))} remaining)\n"
        f"- Protein {round(c.get('protein', 0))}/{c.get('protein_goal')} g, "
        f"Carbs {round(c.get('carbs', 0))}/{c.get('carbs_goal')} g, "
        f"Fat {round(c.get('fat', 0))}/{c.get('fat_goal')} g\n"
        f"- Water {c.get('water')}/{c.get('water_goal')} ml\n"
        f"- Streak: {c.get('streak', 0)} days\n"
        f"- Weight: {c.get('weight')} kg (target {c.get('target_weight')} kg)"
    )


def _coach_fallback(message: str, c: dict) -> str:
    # If the user wrote in Bangla, answer in Bangla.
    if re.search(r"[ঀ-৿]", message or ""):
        return _coach_fallback_bn(message, c)
    m = (message or "").lower()
    rem = round(c.get("remaining", 0))
    p_left = max(0, round(c.get("protein_goal", 0) - c.get("protein", 0)))
    water_left = max(0, c.get("water_goal", 0) - c.get("water", 0))

    if any(w in m for w in ("hi", "hello", "hey")) and len(m) < 12:
        return (f"Hey! 👋 You've got **{rem} kcal** left today and you're on a "
                f"{c.get('streak',0)}-day streak. Ask me what to eat, how your macros "
                "look, or for a meal idea.")
    if "protein" in m:
        return (f"You're at **{round(c.get('protein',0))} g** of your "
                f"{c.get('protein_goal')} g protein goal — about {p_left} g to go. "
                "Easy wins: Greek yogurt (17 g), a protein shake (27 g), chicken breast "
                "(46 g/150 g), or cottage cheese (14 g).")
    if "water" in m or "hydrat" in m:
        if water_left <= 0:
            return "💧 You've already hit your water goal today — nice work staying hydrated!"
        return f"💧 You're {water_left} ml short of your water goal. A glass or two before your next meal will close the gap."
    if "weight" in m or "lose" in m or "gain" in m:
        return (f"Your goal is **{c.get('goal')}** and you're targeting "
                f"{c.get('target_weight')} kg. Consistency beats perfection — staying near "
                f"your {c.get('calorie_goal')} kcal target most days is what moves the trend.")
    if any(w in m for w in ("eat", "meal", "dinner", "lunch", "breakfast", "snack", "hungry")):
        if rem <= 0:
            return ("You're at your calorie goal for today 🎯. If you're hungry, lean on "
                    "high-volume, low-calorie foods: a green salad, berries, or veggies with hummus.")
        if rem < 350:
            return (f"About **{rem} kcal** left — a light option fits best: Greek yogurt with "
                    "berries, a boiled egg + fruit, or a small salad with chicken.")
        return (f"You have **{rem} kcal** to play with. A balanced plate: grilled chicken or "
                "salmon + brown rice/quinoa + a big serving of veg hits protein and fibre nicely.")
    if "how" in m and ("doing" in m or "progress" in m or "today" in m):
        pct = round(c.get("consumed", 0) / max(1, c.get("calorie_goal", 1)) * 100)
        return (f"You're **{pct}%** through your calorie budget ({round(c.get('consumed',0))}"
                f"/{c.get('calorie_goal')} kcal), {p_left} g protein and {water_left} ml water "
                f"left, on a {c.get('streak',0)}-day streak. Solid — keep it steady. 💪")
    return ("I can help with meal ideas, hitting your protein, hydration, and reviewing your "
            f"day. Right now you have **{rem} kcal** and {p_left} g protein left. "
            "What would you like to focus on?")


def _coach_fallback_bn(message: str, c: dict) -> str:
    """Bangla version of the offline coach (same logic, Bangla replies)."""
    m = message or ""
    rem = round(c.get("remaining", 0))
    p_left = max(0, round(c.get("protein_goal", 0) - c.get("protein", 0)))
    water_left = max(0, c.get("water_goal", 0) - c.get("water", 0))

    if any(w in m for w in ("হাই", "হ্যালো", "সালাম", "আসসালাম")) and len(m) < 16:
        return (f"হাই! 👋 আজ আপনার **{rem} ক্যালরি** বাকি আছে আর আপনি "
                f"{c.get('streak',0)} দিনের স্ট্রিকে আছেন। কী খাবেন, ম্যাক্রো কেমন, "
                "নাকি একটা খাবারের আইডিয়া — জিজ্ঞেস করুন।")
    if "প্রোটিন" in m:
        return (f"আপনি **{round(c.get('protein',0))} গ্রাম** প্রোটিনে আছেন "
                f"(লক্ষ্য {c.get('protein_goal')} গ্রাম) — আর প্রায় {p_left} গ্রাম বাকি। "
                "সহজ উপায়: টক দই, ডিম, মুরগির বুকের মাংস, ডাল বা ছোলা।")
    if "পানি" in m:
        if water_left <= 0:
            return "💧 আজ আপনি পানির লক্ষ্য পূরণ করে ফেলেছেন — দারুণ!"
        return f"💧 পানির লক্ষ্য থেকে আর {water_left} ml বাকি। পরের খাবারের আগে এক-দুই গ্লাস খেলেই হয়ে যাবে।"
    if any(w in m for w in ("ওজন", "কমা", "বাড়া")):
        return (f"আপনার লক্ষ্য **{c.get('goal')}**, আর টার্গেট {c.get('target_weight')} কেজি। "
                f"নিয়মিত থাকাটাই আসল — বেশিরভাগ দিন আপনার {c.get('calorie_goal')} ক্যালরির কাছাকাছি "
                "থাকলেই ট্রেন্ড ঠিক পথে চলবে।")
    if any(w in m for w in ("খাব", "খাওয়া", "খাবার", "নাশতা", "দুপুর", "রাত", "ক্ষুধা", "খিদ")):
        if rem <= 0:
            return ("আজকের ক্যালরির লক্ষ্যে পৌঁছে গেছেন 🎯। খিদে পেলে কম-ক্যালরির বেশি-পরিমাণ "
                    "খাবার নিন: সালাদ, শসা, বা ফল।")
        if rem < 350:
            return (f"আর প্রায় **{rem} ক্যালরি** বাকি — হালকা কিছু ভালো হবে: টক দই-ফল, "
                    "একটা সিদ্ধ ডিম, বা ছোট এক প্লেট সালাদ-মুরগি।")
        return (f"আপনার হাতে **{rem} ক্যালরি** আছে। একটা ভারসাম্যপূর্ণ প্লেট: মাছ/মুরগি + "
                "ভাত/রুটি + প্রচুর সবজি — প্রোটিন আর ফাইবার দুটোই ভালো হবে।")
    if "কেমন" in m or "অগ্রগতি" in m or "আজ" in m:
        pct = round(c.get("consumed", 0) / max(1, c.get("calorie_goal", 1)) * 100)
        return (f"আপনি ক্যালরি বাজেটের **{pct}%** শেষ করেছেন ({round(c.get('consumed',0))}"
                f"/{c.get('calorie_goal')} ক্যালরি), প্রোটিন {p_left} গ্রাম আর পানি {water_left} ml বাকি, "
                f"{c.get('streak',0)} দিনের স্ট্রিকে আছেন। দারুণ চলছে — এভাবেই রাখুন। 💪")
    return ("আমি খাবারের আইডিয়া, প্রোটিন, পানি আর আপনার দিনের হিসাব নিয়ে সাহায্য করতে পারি। "
            f"এখন আপনার **{rem} ক্যালরি** আর {p_left} গ্রাম প্রোটিন বাকি। কোনটা নিয়ে কথা বলবেন?")
