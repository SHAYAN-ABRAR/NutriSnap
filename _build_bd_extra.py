"""
Builds core/foods_bd_extra.py — extra Bangladeshi dishes from the Wikipedia
"List of Bangladeshi dishes" page (Fish items, Sweets & desserts, Snacks &
street food) that weren't already in the catalog.

Images: prefer the EXACT Wikimedia Commons File named on that page; otherwise
force a relevance-scored Commons search. Gentle (bot UA, retries, spacing).
Run: python _build_bd_extra.py
"""
import re
import json
import time
import requests

HEADERS = {"User-Agent": "NutriSnapBot/1.0 (food catalog builder; +https://github.com/nutrisnap)"}
BAD = ("icon", "logo", "map", "flag", "coat_of_arms", "symbol", "stamp", ".svg",
       ".pdf", ".djvu", "magazine", "library", "book", "journal", "songster",
       "label", "packaging", "menu", "sign", "poster", "diagram", "chart")
STOP = {"with", "food", "dish", "the", "and", "fresh", "style", "curry", "macher",
        "machh", "mach", "jhol", "bhuna", "river", "fish"}
COMMONS = "https://commons.wikimedia.org/w/api.php"

# (name, emoji, unit, kcal, p, c, f, fib, cat, exact_commons_file_or_None, search_hint)
CATALOG = [
    # --------------------------- Fish items ---------------------------
    ("Pangas Bhuna (River Catfish)", "🐟", "1 piece", 250, 22, 6, 15, 1, "Bangladeshi",
     "Nodir (River) Pangas Bhuna.jpg", "pangas fish curry bengali"),
    ("Horioh Mach (Mustard Fish Curry)", "🐟", "1 piece", 210, 20, 5, 12, 1, "Bangladeshi",
     "Sorshe diye khoyra machher jhal.jpg", "shorshe bata mach mustard fish curry bengali"),
    ("Magur Macher Jhol (Catfish Curry)", "🐟", "1 bowl", 180, 22, 6, 7, 1, "Bangladeshi",
     "Magur Macher Jhol.jpg", "magur fish curry bengali"),
    ("Shing Macher Jhol (Catfish Curry)", "🐟", "1 bowl", 175, 21, 5, 7, 1, "Bangladeshi",
     "Shing Macher Jhol.jpg", "shing fish curry bengali"),
    # ----------------------- Snacks & street food -----------------------
    ("Doi Fuchka (Yogurt Fuchka)", "🥣", "1 plate", 260, 8, 40, 8, 4, "Bangladeshi",
     "Doi fuchka. .jpg", "doi fuchka dahi puri"),
]

# Existing catalog entries that are missing a photo — fetch one and patch separately.
PATCH = [
    ("Dimer Chop (Egg chop)", "Indian Egg Chop(Egg snacks) – KOLKATA.jpg",
     "egg chop dimer chop bengali snack"),
]


def file_thumb(filename, session, width=400):
    """Resolve an exact 'File:Name.jpg' to a thumbnail URL via Commons imageinfo."""
    if not filename:
        return ""
    title = "File:" + filename.strip()
    for k in range(3):
        try:
            r = session.get(COMMONS, params={"action": "query", "format": "json",
                "titles": title, "prop": "imageinfo", "iiprop": "url|mime",
                "iiurlwidth": width, "redirects": 1}, headers=HEADERS, timeout=25)
            if r.status_code == 429:
                time.sleep(5 * (k + 1)); continue
            pages = (r.json().get("query") or {}).get("pages") or {}
            for p in pages.values():
                ii = (p.get("imageinfo") or [{}])[0]
                if ii.get("mime") == "image/svg+xml":
                    return ""
                return ii.get("thumburl", "") or ""
        except Exception:
            time.sleep(4 * (k + 1))
    return ""


def commons_candidates(q, session, tries=4):
    for k in range(tries):
        try:
            r = session.get(COMMONS, params={"action": "query", "format": "json",
                "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 15,
                "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 400},
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


def commons_best(name, hint, session):
    """Force an image from Commons by relevance-scoring search results."""
    base = re.sub(r"\(.*?\)", "", name).strip()
    tokens = {w for w in re.findall(r"[a-z]+", (base + " " + hint).lower())
              if len(w) >= 4 and w not in STOP}
    best_url, best_score = "", 0
    for q in (hint, base):
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


def resolve_image(name, exact_file, hint, session):
    img = file_thumb(exact_file, session)
    if img:
        return img, "file"
    img = commons_best(name, hint, session)
    return img, ("srch" if img else "none")


def main():
    session = requests.Session()
    items = []
    for (name, emoji, unit, kcal, p, c, f, fib, cat, exact, hint) in CATALOG:
        img, src = resolve_image(name, exact, hint, session)
        items.append({"name": name, "emoji": emoji, "unit": unit, "calories": kcal,
                      "protein": p, "carbs": c, "fat": f, "fiber": fib,
                      "cat": cat, "image": img})
        print(f"  [{src:4s}] {name}")
        time.sleep(0.4)

    with open("core/foods_bd_extra.py", "w", encoding="utf-8") as fh:
        fh.write('"""Extra Bangladeshi dishes (fish/sweets/snacks) from the Wikipedia\n')
        fh.write('"List of Bangladeshi dishes". Auto-generated by _build_bd_extra.py."""\n\n')
        fh.write("FOODS_BD_EXTRA = [\n")
        for it in items:
            fh.write("    " + json.dumps(it, ensure_ascii=False) + ",\n")
        fh.write("]\n")
    n = sum(1 for it in items if it["image"])
    print(f"\nWrote core/foods_bd_extra.py — {len(items)} items, {n} with images.")

    # Resolve images for existing image-less entries; print so we can patch by hand.
    print("\n--- Images for existing entries to patch ---")
    for (name, exact, hint) in PATCH:
        img, src = resolve_image(name, exact, hint, session)
        print(f"  [{src:4s}] {name}\n        {img}")


if __name__ == "__main__":
    main()
