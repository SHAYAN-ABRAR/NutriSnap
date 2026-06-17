"""Targeted, *relevance-scored* image resolver for the curated BD dishes.

For each dish below it searches Wikimedia Commons and accepts only the photo whose
FILENAME best matches the dish's words (token overlap). If nothing genuinely matches,
the dish is left as a clean emoji rather than a wrong photo. Wiki lead images already
in foods_bd.py for other dishes are untouched. Run: python _fillgaps.py
"""
import re
import json
import time
import requests

from core import foods_bd

HEADERS = {"User-Agent": "NutriSnapBot/1.0 (food catalog builder; +https://github.com/nutrisnap)"}
BAD = ("icon", "logo", "map", "flag", "coat_of_arms", "symbol", "stamp", ".svg",
       "label", "packaging", "menu", "sign", "poster", "diagram", "chart", "peon", "flower")
STOP = {"with", "food", "dish", "the", "and", "fresh", "style", "curry", "spicy",
        "bhuna", "diye", "fried", "mach"}

# dish -> Commons search queries (the dish's own name words drive relevance scoring)
QMAP = {
    "Beef Curry": ["beef curry", "beef bhuna"],
    "Chicken Roast": ["roast chicken", "chicken roast"],
    "Chicken Curry": ["chicken curry"],
    "Mutton Curry": ["mutton curry", "goat curry"],
    "Gorur Kolija Bhuna (Liver)": ["liver fry", "beef liver curry"],
    "Egg Curry (Dim Bhuna)": ["egg curry", "anda curry"],
    "Aloo Bhorta": ["aloo bharta", "alu bhorta"],
    "Begun Bhorta": ["baingan bharta", "begun bharta"],
    "Mixed Vegetables (Shobji)": ["mixed vegetable curry", "niramish"],
    "Cholar Dal": ["cholar dal", "chana dal"],
    "Mashkalai Dal": ["mash kalai dal", "urad dal"],
    "Piyaju": ["piyaju", "lentil fritter"],
    "Dal Puri": ["dal puri", "dal poori"],
    "Patishapta": ["patishapta pitha", "patishapta"],
    "Nakshi Pitha": ["nakshi pitha"],
    "Muri Laru": ["murir moa", "puffed rice ball"],
    "Wood Apple (Bel)": ["bael fruit", "wood apple"],
    "Chicken Patties": ["chicken patties", "chicken puff pastry"],
    "Shutki Bhuna (Dried fish)": ["shutki", "dried fish curry"],
    "Lal Shak Bhaja": ["red amaranth", "amaranth leaves cooked"],
    "Zinger Burger": ["chicken burger", "crispy chicken burger"],
    "Dimer Chop (Egg chop)": ["egg chop", "egg cutlet"],
    # left intentionally as emoji (no reliable distinct Commons photo):
    #   Beef Chui Jhal, Fulkopi diye Shing Mach
}
FORCE_EMOJI = {"Beef Chui Jhal", "Fulkopi diye Shing Mach"}


def tokens_for(name, queries):
    text = re.sub(r"\(.*?\)", "", name) + " " + " ".join(queries)
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 4 and w not in STOP}


def candidates(q, tries=4):
    for k in range(tries):
        try:
            r = requests.get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "format": "json", "generator": "search",
                "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 15,
                "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 320,
            }, headers=HEADERS, timeout=25)
            if r.status_code == 429:
                time.sleep(6 * (k + 1)); continue
            pages = (r.json().get("query") or {}).get("pages") or {}
            out = []
            for p in sorted(pages.values(), key=lambda x: x.get("index", 999)):
                ii = (p.get("imageinfo") or [{}])[0]
                out.append((p.get("title", ""), ii.get("thumburl", ""), ii.get("mime", "")))
            return out
        except Exception:
            time.sleep(5 * (k + 1))
    return []


def best_image(queries, tokens):
    """Highest token-overlap Commons photo across the queries (must score >= 1)."""
    best_url, best_title, best_score = "", "", 0
    for q in queries:
        for title, thumb, mime in candidates(q):
            tl = title.lower()
            if not thumb or mime == "image/svg+xml" or any(b in tl for b in BAD):
                continue
            score = sum(1 for t in tokens if t in tl)
            if score > best_score:
                best_url, best_title, best_score = thumb, title, score
        time.sleep(1.2)
        if best_score >= 2:        # strong match found, stop early
            break
    return best_url, best_title, best_score


def main():
    items = [dict(x) for x in foods_bd.FOODS_BD]
    kept = cleared = 0
    for it in items:
        name = it["name"]
        if name in FORCE_EMOJI:
            if it["image"]:
                cleared += 1
            it["image"] = ""
            print(f"  [emo] {name}  (forced emoji)")
            continue
        if name not in QMAP:
            continue
        tokens = tokens_for(name, QMAP[name])
        url, title, score = best_image(QMAP[name], tokens)
        if url:
            it["image"] = url
            kept += 1
            print(f"  [ok ] {name:30s} (score {score}) <- {title[:46].encode('ascii','ignore').decode()}")
        else:
            if it["image"]:
                cleared += 1
            it["image"] = ""
            print(f"  [emo] {name:30s} (no relevant photo)")
        time.sleep(1.0)

    with open("core/foods_bd.py", "w", encoding="utf-8") as fh:
        fh.write('"""Bangladeshi dishes, BD fruits and global savory foods.\n')
        fh.write("Image URLs are Wikimedia/Commons thumbnails (built by _build_bd.py + _fillgaps.py).\n")
        fh.write('Each item: name, emoji, unit, calories, protein, carbs, fat, fiber, cat, image."""\n\n')
        fh.write("FOODS_BD = [\n")
        for it in items:
            fh.write("    " + json.dumps(it, ensure_ascii=False) + ",\n")
        fh.write("]\n")
    total = sum(1 for x in items if x["image"])
    print(f"\nResolved {kept} relevant, cleared {cleared} wrong. foods_bd.py now {total}/{len(items)} with images.")


if __name__ == "__main__":
    main()
