"""
Builds core/foods_extra.py — juices/drinks, chocolates & sweets, and more Bengali
misty. Images: Wikipedia lead image (trusted) else a relevance-scored Commons photo,
else emoji. Self-contained & gentle (bot UA, retries, spacing). Run: python _build_extra.py
"""
import re
import json
import time
import requests

HEADERS = {"User-Agent": "NutriSnapBot/1.0 (food catalog builder; +https://github.com/nutrisnap)"}
BAD = ("icon", "logo", "map", "flag", "coat_of_arms", "symbol", "stamp", ".svg",
       "label", "packaging", "menu", "sign", "poster", "diagram", "chart", "peon", "flower")
STOP = {"with", "food", "dish", "the", "and", "fresh", "style", "plain", "cold", "iced"}

# (name, emoji, unit, kcal, p, c, f, fib, cat, wiki_title_or_None)
CATALOG = [
    # ----------------------- Drinks / juices -----------------------
    ("Orange Juice", "🧃", "1 glass", 110, 2, 26, 0, 0, "Drinks", "Orange juice"),
    ("Apple Juice", "🧃", "1 glass", 115, 0, 28, 0, 0, "Drinks", "Apple juice"),
    ("Mango Juice", "🥤", "1 glass", 130, 1, 33, 0, 0, "Drinks", "Mango juice"),
    ("Watermelon Juice", "🍉", "1 glass", 80, 1, 20, 0, 0, "Drinks", None),
    ("Pineapple Juice", "🍍", "1 glass", 130, 1, 32, 0, 0, "Drinks", "Pineapple juice"),
    ("Pomegranate Juice", "🧃", "1 glass", 134, 0, 33, 0, 0, "Drinks", "Pomegranate juice"),
    ("Lemonade (Lebur Shorbot)", "🍋", "1 glass", 100, 0, 26, 0, 0, "Drinks", "Lemonade"),
    ("Sugarcane Juice", "🥤", "1 glass", 180, 0, 45, 0, 0, "Drinks", "Sugarcane juice"),
    ("Coconut Water (Dab)", "🥥", "1 glass", 46, 2, 9, 0, 0, "Drinks", "Coconut water"),
    ("Mango Lassi", "🥭", "1 glass", 210, 6, 38, 4, 0, "Drinks", "Lassi"),
    ("Fruit Smoothie", "🥤", "1 glass", 220, 4, 45, 3, 2, "Drinks", "Smoothie"),
    ("Cola (Soft Drink)", "🥤", "1 can", 140, 0, 39, 0, 0, "Drinks", "Cola"),
    ("Lemon-Lime Soda", "🥤", "1 can", 140, 0, 38, 0, 0, "Drinks", "Lemon-lime drink"),
    ("Energy Drink", "⚡", "1 can", 110, 0, 28, 0, 0, "Drinks", "Energy drink"),
    ("Iced Tea", "🧊", "1 glass", 90, 0, 22, 0, 0, "Drinks", "Iced tea"),
    ("Chocolate Milkshake", "🥤", "1 glass", 350, 9, 50, 12, 1, "Drinks", "Milkshake"),
    ("Cold Coffee", "🧋", "1 glass", 180, 5, 25, 6, 0, "Drinks", "Iced coffee"),
    ("Green Tea", "🍵", "1 cup", 2, 0, 0, 0, 0, "Drinks", "Green tea"),
    # ----------------------- Chocolates & sweets (global) -----------------------
    ("Milk Chocolate", "🍫", "40 g", 215, 3, 24, 12, 1, "Sweets", "Chocolate bar"),
    ("Chocolate Bar", "🍫", "50 g", 250, 3, 30, 14, 2, "Sweets", "Chocolate bar"),
    ("KitKat", "🍫", "45 g bar", 230, 3, 27, 12, 1, "Sweets", "Kit Kat"),
    ("Snickers", "🍫", "50 g bar", 250, 4, 33, 12, 1, "Sweets", "Snickers"),
    ("Candy / Toffee", "🍬", "5 pieces", 100, 0, 25, 1, 0, "Sweets", "Candy"),
    ("Gummy Bears", "🐻", "30 g", 100, 2, 23, 0, 0, "Sweets", "Gummy bear"),
    ("Lollipop", "🍭", "1 piece", 60, 0, 15, 0, 0, "Sweets", "Lollipop"),
    ("Chocolate Cookie", "🍪", "2 cookies", 160, 2, 22, 8, 1, "Sweets", "Cookie"),
    ("Brownie", "🟫", "1 piece", 250, 3, 32, 13, 1, "Sweets", "Chocolate brownie"),
    ("Cupcake", "🧁", "1 piece", 200, 2, 30, 9, 0, "Sweets", "Cupcake"),
    ("Chocolate Cake", "🍰", "1 slice", 350, 4, 50, 16, 2, "Sweets", "Chocolate cake"),
    ("Cheesecake", "🍰", "1 slice", 320, 6, 26, 22, 1, "Sweets", "Cheesecake"),
    ("Macaron", "🍬", "2 pieces", 140, 3, 20, 6, 0, "Sweets", "Macaron"),
    ("Waffle", "🧇", "1 waffle", 220, 5, 30, 9, 1, "Sweets", "Waffle"),
    ("Gulab Jamun", "🟤", "2 pieces", 300, 4, 50, 10, 0, "Sweets", "Gulab jamun"),
    ("Kulfi", "🍡", "1 piece", 200, 5, 22, 11, 0, "Sweets", "Kulfi"),
    # ----------------------- More Bengali misty -----------------------
    ("Kalojam", "🟤", "2 pieces", 280, 4, 44, 10, 0, "Bangladeshi", "Kala jamun"),
    ("Kheer Kadam", "🟡", "1 piece", 180, 5, 28, 6, 0, "Bangladeshi", None),
    ("Balushahi", "🟤", "1 piece", 260, 3, 36, 12, 0, "Bangladeshi", "Balushahi"),
    ("Chhanar Jilapi", "🍥", "2 pieces", 250, 5, 38, 9, 0, "Bangladeshi", "Chhena jalebi"),
    ("Langcha", "🟤", "1 piece", 230, 4, 36, 8, 0, "Bangladeshi", "Langcha"),
    ("Mihidana", "🟡", "50 g", 200, 2, 40, 5, 0, "Bangladeshi", "Mihidana"),
    ("Sitabhog", "🍚", "50 g", 190, 3, 38, 4, 0, "Bangladeshi", "Sitabhog"),
    ("Amriti (Jhuri)", "🍥", "2 pieces", 240, 3, 42, 8, 0, "Bangladeshi", "Imarti"),
    ("Khaja", "🟤", "1 piece", 200, 2, 32, 8, 0, "Bangladeshi", "Khaja"),
    ("Rajbhog", "🤍", "2 pieces", 260, 6, 42, 7, 0, "Bangladeshi", "Rajbhog"),
    ("Malai Chop", "🤍", "2 pieces", 270, 6, 36, 11, 0, "Bangladeshi", None),
    ("Shor Bhaja", "🟤", "1 piece", 220, 4, 28, 10, 0, "Bangladeshi", None),
    ("Doi (Plain Yogurt)", "🥛", "1 cup", 100, 5, 12, 3, 0, "Bangladeshi", "Dahi (curd)"),
    ("Khejur Gur (Date Molasses)", "🍯", "1 tbsp", 60, 0, 15, 0, 0, "Bangladeshi", "Jaggery"),
]

API = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"


def wiki_thumbs(titles, session):
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        try:
            r = session.get(API, params={"action": "query", "format": "json",
                "prop": "pageimages", "piprop": "thumbnail", "pithumbsize": 320,
                "redirects": 1, "titles": "|".join(chunk)}, headers=HEADERS, timeout=30)
            data = (r.json() or {}).get("query", {})
            alias = {}
            for n in data.get("normalized", []):
                alias[n["from"]] = n["to"]
            for rd in data.get("redirects", []):
                alias[rd["from"]] = rd["to"]
            t2t = {}
            for _, p in (data.get("pages") or {}).items():
                src = (p.get("thumbnail") or {}).get("source")
                if src:
                    t2t[p["title"]] = src

            def resolve(t):
                seen = set()
                while t in alias and t not in seen:
                    seen.add(t); t = alias[t]
                return t
            for t in chunk:
                out[t] = t2t.get(resolve(t), "")
        except Exception:
            for t in chunk:
                out[t] = ""
        time.sleep(0.5)
    return out


def commons_candidates(q, session, tries=4):
    for k in range(tries):
        try:
            r = session.get(COMMONS, params={"action": "query", "format": "json",
                "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 15,
                "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 320},
                headers=HEADERS, timeout=25)
            if r.status_code == 429:
                time.sleep(6 * (k + 1)); continue
            pages = (r.json().get("query") or {}).get("pages") or {}
            return [(p.get("title", ""), (p.get("imageinfo") or [{}])[0].get("thumburl", ""),
                     (p.get("imageinfo") or [{}])[0].get("mime", ""))
                    for p in sorted(pages.values(), key=lambda x: x.get("index", 999))]
        except Exception:
            time.sleep(5 * (k + 1))
    return []


def commons_best(name, cat, session):
    base = re.sub(r"\(.*?\)", "", name).strip()
    tokens = {w for w in re.findall(r"[a-z]+", base.lower()) if len(w) >= 4 and w not in STOP}
    suffix = " drink" if cat == "Drinks" else " sweet"
    best_url, best_score = "", 0
    for q in (base, base + suffix):
        for title, thumb, mime in commons_candidates(q, session):
            tl = title.lower()
            if not thumb or mime == "image/svg+xml" or any(b in tl for b in BAD):
                continue
            score = sum(1 for t in tokens if t in tl)
            if score > best_score:
                best_url, best_score = thumb, score
        time.sleep(1.0)
        if best_score >= 2:
            break
    return best_url


def main():
    session = requests.Session()
    titles = sorted({t for *_, t in CATALOG if t})
    wt = wiki_thumbs(titles, session)
    items = []
    for (name, emoji, unit, kcal, p, c, f, fib, cat, title) in CATALOG:
        img = wt.get(title, "") if title else ""
        src = "wiki" if img else ""
        if not img:
            img = commons_best(name, cat, session)
            src = "cmns" if img else "emo"
        items.append({"name": name, "emoji": emoji, "unit": unit, "calories": kcal,
                      "protein": p, "carbs": c, "fat": f, "fiber": fib,
                      "cat": cat, "image": img})
        print(f"  [{src:4s}] {name}")

    with open("core/foods_extra.py", "w", encoding="utf-8") as fh:
        fh.write('"""Extra catalog: drinks/juices, chocolates & sweets, more Bengali misty.\n')
        fh.write('Auto-generated by _build_extra.py. Same item shape as foods_bd."""\n\n')
        fh.write("FOODS_EXTRA = [\n")
        for it in items:
            fh.write("    " + json.dumps(it, ensure_ascii=False) + ",\n")
        fh.write("]\n")
    n = sum(1 for it in items if it["image"])
    print(f"\nWrote core/foods_extra.py — {len(items)} items, {n} with images.")


if __name__ == "__main__":
    main()
