"""
Build script: authors the Bangladeshi + fruits + fast-food catalog, fetches a real
Wikimedia thumbnail for each item that has a Wikipedia page, and writes
core/foods_bd.py with the final data (image URLs baked in; emoji as fallback).

Run once:  python _build_bd.py
"""
import re
import json
import time
import requests

HEADERS = {"User-Agent": "NutriSnap/1.0 (calorie tracker; educational)"}

# (name, emoji, unit, kcal, protein, carbs, fat, fiber, category, wiki_title_or_None)
CATALOG = [
    # ---------------- Bangladeshi · Rice ----------------
    ("Plain Rice (Bhaat)", "🍚", "1 cup cooked", 205, 4, 45, 0, 1, "Bangladeshi", "Cooked rice"),
    ("Panta Bhat", "🍚", "1 bowl", 180, 4, 40, 0, 2, "Bangladeshi", "Panta bhat"),
    ("Bhuna Khichuri", "🍲", "1 plate", 430, 14, 60, 14, 6, "Bangladeshi", "Khichdi"),
    ("Plain Khichuri", "🍲", "1 bowl", 320, 11, 52, 7, 6, "Bangladeshi", "Khichdi"),
    ("Polao", "🍚", "1 plate", 380, 7, 58, 13, 2, "Bangladeshi", "Pilaf"),
    ("Morog Polao", "🍗", "1 plate", 560, 28, 60, 23, 2, "Bangladeshi", "Morog Polao"),
    ("Chicken Biryani", "🍛", "1 plate", 620, 30, 70, 24, 3, "Bangladeshi", "Biryani"),
    ("Kacchi Biriyani", "🍛", "1 plate", 780, 35, 78, 36, 3, "Bangladeshi", "Kacchi biryani"),
    ("Beef Tehari", "🍛", "1 plate", 700, 30, 72, 32, 3, "Bangladeshi", "Tehari (dish)"),
    # ---------------- Bangladeshi · Fish ----------------
    ("Sorshe Ilish", "🐟", "1 piece + gravy", 320, 24, 4, 23, 0, "Bangladeshi", "Sorshe Ilish"),
    ("Ilish Bhaja (Fried Hilsa)", "🐟", "1 piece", 290, 22, 1, 22, 0, "Bangladeshi", "Ilish"),
    ("Macher Jhol (Fish curry)", "🐟", "1 bowl", 240, 22, 6, 14, 1, "Bangladeshi", "Macher jhol"),
    ("Rui Bhaja (Fried Rohu)", "🐟", "1 piece", 260, 24, 2, 18, 0, "Bangladeshi", "Rohu"),
    ("Koi Macher Curry", "🐟", "1 bowl", 230, 21, 5, 14, 1, "Bangladeshi", None),
    ("Chingri Malai Curry", "🦐", "1 bowl", 360, 22, 9, 26, 1, "Bangladeshi", "Chingri malai curry"),
    ("Shutki Bhuna (Dried fish)", "🐟", "1 serving", 250, 26, 6, 14, 1, "Bangladeshi", None),
    ("Lau Chingri", "🦐", "1 bowl", 190, 12, 12, 11, 3, "Bangladeshi", None),
    # ---------------- Bangladeshi · Meat ----------------
    ("Beef Curry", "🥩", "1 bowl", 360, 28, 6, 25, 1, "Bangladeshi", "Beef curry"),
    ("Beef Kala Bhuna", "🥩", "1 bowl", 450, 30, 8, 34, 1, "Bangladeshi", "Kala bhuna"),
    ("Beef Chui Jhal", "🥩", "1 bowl", 420, 29, 7, 31, 1, "Bangladeshi", None),
    ("Gorur Kolija Bhuna (Liver)", "🥩", "1 bowl", 300, 28, 6, 18, 0, "Bangladeshi", None),
    ("Chicken Curry", "🍗", "1 bowl", 300, 27, 6, 19, 1, "Bangladeshi", "Chicken curry"),
    ("Chicken Roast", "🍗", "1 piece", 380, 30, 12, 24, 1, "Bangladeshi", None),
    ("Mutton Curry", "🍖", "1 bowl", 420, 28, 6, 32, 1, "Bangladeshi", "Mutton curry"),
    ("Egg Curry (Dim Bhuna)", "🥚", "2 eggs + gravy", 260, 14, 8, 19, 1, "Bangladeshi", None),
    # ---------------- Bangladeshi · Veg / Bhorta ----------------
    ("Aloo Bhorta", "🥔", "1 serving", 150, 3, 22, 6, 3, "Bangladeshi", "Bhorta (food)"),
    ("Begun Bhorta", "🍆", "1 serving", 130, 2, 12, 9, 4, "Bangladeshi", "Bhorta (food)"),
    ("Lal Shak Bhaja", "🥬", "1 serving", 110, 3, 10, 7, 4, "Bangladeshi", None),
    ("Mixed Vegetables (Shobji)", "🥗", "1 bowl", 160, 4, 18, 9, 5, "Bangladeshi", None),
    ("Fulkopi diye Shing Mach", "🐟", "1 bowl", 240, 20, 10, 13, 3, "Bangladeshi", None),
    # ---------------- Bangladeshi · Dal ----------------
    ("Dal (Lentils)", "🍲", "1 bowl", 180, 11, 26, 3, 8, "Bangladeshi", "Dal"),
    ("Cholar Dal", "🍲", "1 bowl", 230, 12, 32, 6, 9, "Bangladeshi", None),
    ("Mashkalai Dal", "🍲", "1 bowl", 200, 12, 28, 4, 8, "Bangladeshi", None),
    ("Beef Haleem", "🍲", "1 bowl", 380, 24, 34, 16, 5, "Bangladeshi", "Haleem"),
    # ---------------- Bangladeshi · Bread ----------------
    ("Ruti (Roti)", "🫓", "1 piece", 110, 3, 22, 1, 3, "Bangladeshi", "Roti"),
    ("Paratha", "🫓", "1 piece", 260, 5, 30, 13, 2, "Bangladeshi", "Paratha"),
    ("Luchi", "🫓", "2 pieces", 280, 5, 32, 15, 1, "Bangladeshi", "Luchi"),
    ("Naan", "🫓", "1 piece", 290, 9, 50, 6, 2, "Bangladeshi", "Naan"),
    ("Mughlai Paratha", "🫓", "1 piece", 420, 14, 38, 24, 2, "Bangladeshi", "Mughlai paratha"),
    # ---------------- Bangladeshi · Snacks / Street ----------------
    ("Fuchka", "🥟", "1 plate", 280, 7, 45, 8, 5, "Bangladeshi", "Panipuri"),
    ("Chotpoti", "🍛", "1 plate", 300, 12, 42, 9, 8, "Bangladeshi", "Chotpoti"),
    ("Jhalmuri", "🥜", "1 cup", 220, 6, 30, 9, 4, "Bangladeshi", "Jhalmuri"),
    ("Bhelpuri", "🥙", "1 plate", 250, 6, 38, 8, 5, "Bangladeshi", "Bhelpuri"),
    ("Samosa", "🥟", "1 piece", 130, 3, 15, 7, 2, "Bangladeshi", "Samosa"),
    ("Singara", "🥟", "1 piece", 140, 3, 16, 7, 2, "Bangladeshi", "Samosa"),
    ("Beguni", "🍆", "2 pieces", 160, 3, 16, 10, 2, "Bangladeshi", "Beguni"),
    ("Piyaju", "🧅", "3 pieces", 150, 5, 16, 8, 3, "Bangladeshi", None),
    ("Dimer Chop (Egg chop)", "🥚", "1 piece", 180, 7, 14, 11, 2, "Bangladeshi", None),
    ("Dal Puri", "🫓", "2 pieces", 240, 6, 30, 11, 3, "Bangladeshi", None),
    ("Chicken Roll", "🌯", "1 roll", 330, 16, 32, 16, 2, "Bangladeshi", "Kati roll"),
    # ---------------- Bangladeshi · Pitha ----------------
    ("Bhapa Pitha", "🍡", "1 piece", 180, 3, 38, 3, 2, "Bangladeshi", "Bhapa pitha"),
    ("Chitoi Pitha", "🥮", "1 piece", 120, 3, 26, 1, 1, "Bangladeshi", "Chitoi pitha"),
    ("Patishapta", "🥮", "1 piece", 200, 4, 30, 7, 1, "Bangladeshi", "Patishapta"),
    ("Nakshi Pitha", "🍡", "1 piece", 160, 2, 30, 4, 1, "Bangladeshi", None),
    # ---------------- Bangladeshi · Sweets ----------------
    ("Roshogolla", "🍥", "2 pieces", 220, 5, 40, 5, 0, "Bangladeshi", "Rasgulla"),
    ("Chomchom", "🍮", "1 piece", 170, 4, 28, 5, 0, "Bangladeshi", "Cham cham"),
    ("Rasmalai", "🍮", "2 pieces", 280, 7, 34, 13, 0, "Bangladeshi", "Rasmalai"),
    ("Mishti Doi", "🍶", "1 cup", 230, 6, 40, 5, 0, "Bangladeshi", "Mishti Doi"),
    ("Sandesh", "🍬", "2 pieces", 200, 6, 30, 6, 0, "Bangladeshi", "Sandesh (confectionery)"),
    ("Jilapi", "🍥", "100 g", 350, 2, 60, 12, 0, "Bangladeshi", "Jalebi"),
    ("Payesh (Kheer)", "🍚", "1 bowl", 270, 7, 44, 7, 1, "Bangladeshi", "Kheer"),
    ("Laddu", "🟡", "1 piece", 180, 3, 26, 8, 1, "Bangladeshi", "Laddu"),
    ("Pera", "🍬", "2 pieces", 190, 5, 28, 7, 0, "Bangladeshi", "Peda"),
    ("Muri Laru", "🟤", "1 piece", 150, 2, 28, 4, 1, "Bangladeshi", None),
    # ---------------- Bangladeshi · Drinks ----------------
    ("Borhani", "🥛", "1 glass", 110, 4, 12, 5, 0, "Bangladeshi", "Borhani"),
    ("Lassi", "🥤", "1 glass", 180, 6, 30, 4, 0, "Bangladeshi", "Lassi"),
    ("Faluda", "🍨", "1 glass", 320, 7, 52, 9, 1, "Bangladeshi", "Faluda"),
    ("Malai Cha (Milk Tea)", "🍵", "1 cup", 120, 4, 16, 4, 0, "Bangladeshi", "Tea"),

    # ---------------- Fruits common in Bangladesh ----------------
    ("Mango (Aam)", "🥭", "1 medium", 150, 1, 38, 1, 4, "Fruit", "Mango"),
    ("Jackfruit (Kathal)", "🟡", "1 cup", 155, 2, 40, 1, 3, "Fruit", "Jackfruit"),
    ("Guava (Peyara)", "🟢", "1 medium", 110, 4, 24, 2, 9, "Fruit", "Guava"),
    ("Litchi (Lychee)", "🔴", "10 pieces", 66, 1, 17, 0, 1, "Fruit", "Lychee"),
    ("Papaya (Pepe)", "🟠", "1 cup", 62, 1, 16, 0, 2, "Fruit", "Papaya"),
    ("Watermelon (Tormuj)", "🍉", "1 cup", 46, 1, 12, 0, 1, "Fruit", "Watermelon"),
    ("Pineapple (Anaras)", "🍍", "1 cup", 82, 1, 22, 0, 2, "Fruit", "Pineapple"),
    ("Coconut (Narikel)", "🥥", "50 g", 175, 2, 8, 17, 4, "Fruit", "Coconut"),
    ("Sapodilla (Sofeda)", "🟤", "1 medium", 140, 1, 34, 2, 9, "Fruit", "Sapodilla"),
    ("Wood Apple (Bel)", "🟤", "1 cup", 140, 3, 32, 1, 5, "Fruit", "Bael"),
    ("Star Fruit (Kamranga)", "⭐", "1 medium", 30, 1, 7, 0, 3, "Fruit", "Carambola"),
    ("Black Plum (Jam)", "🟣", "1 cup", 70, 1, 18, 0, 1, "Fruit", "Syzygium cumini"),
    ("Pomelo (Jambura)", "🟡", "1 cup", 72, 1, 18, 0, 2, "Fruit", "Pomelo"),
    ("Java Apple (Jamrul)", "🔔", "2 pieces", 50, 1, 12, 0, 1, "Fruit", "Syzygium samarangense"),
    ("Hog Plum (Amra)", "🟢", "1 medium", 45, 1, 11, 0, 2, "Fruit", "Spondias dulcis"),
    ("Tamarind (Tetul)", "🟤", "30 g", 70, 1, 18, 0, 2, "Fruit", "Tamarind"),
    ("Jujube (Boroi)", "🟤", "5 pieces", 80, 1, 20, 0, 2, "Fruit", "Jujube"),
    ("Sugarcane (Akh)", "🎋", "1 cup juice", 180, 0, 45, 0, 0, "Fruit", "Sugarcane"),
    ("Custard Apple (Ata)", "🟢", "1 medium", 150, 3, 36, 1, 7, "Fruit", "Annona reticulata"),
    ("Date (Khejur)", "🌰", "3 pieces", 200, 2, 54, 0, 5, "Fruit", "Date palm"),
    ("Orange (Komola)", "🍊", "1 medium", 62, 1, 15, 0, 3, "Fruit", "Orange (fruit)"),

    # ---------------- Western / global savory (easy to find in BD) ----------------
    ("Club Sandwich", "🥪", "1 sandwich", 480, 24, 44, 24, 3, "Fast food", "Club sandwich"),
    ("Chicken Sandwich", "🥪", "1 sandwich", 400, 22, 38, 18, 2, "Fast food", "Chicken sandwich"),
    ("Egg Sandwich", "🥪", "1 sandwich", 300, 13, 30, 14, 2, "Fast food", "Egg sandwich"),
    ("Grilled Cheese Sandwich", "🥪", "1 sandwich", 400, 14, 33, 24, 2, "Fast food", "Cheese sandwich"),
    ("Submarine Sandwich", "🥖", "6 inch", 420, 22, 46, 16, 3, "Fast food", "Submarine sandwich"),
    ("Beef Burger", "🍔", "1 burger", 550, 28, 42, 30, 3, "Fast food", "Hamburger"),
    ("Chicken Burger", "🍔", "1 burger", 500, 26, 44, 24, 3, "Fast food", "Chicken sandwich"),
    ("Zinger Burger", "🍔", "1 burger", 540, 27, 46, 27, 3, "Fast food", None),
    ("Hot Dog", "🌭", "1 hot dog", 290, 10, 24, 17, 1, "Fast food", "Hot dog"),
    ("Fried Chicken", "🍗", "1 piece", 320, 22, 11, 21, 1, "Fast food", "Fried chicken"),
    ("Chicken Nuggets", "🍗", "6 pieces", 270, 14, 16, 17, 1, "Fast food", "Chicken nugget"),
    ("Shawarma", "🌯", "1 wrap", 470, 26, 44, 21, 3, "Fast food", "Shawarma"),
    ("Spring Roll", "🥢", "2 pieces", 200, 5, 24, 10, 2, "Fast food", "Spring roll"),
    ("Momo (Dumplings)", "🥟", "6 pieces", 280, 12, 36, 10, 2, "Fast food", "Momo (food)"),
    ("Chicken Chow Mein", "🍜", "1 plate", 480, 20, 60, 18, 4, "Fast food", "Chow mein"),
    ("Chicken Fried Rice", "🍚", "1 plate", 520, 18, 68, 18, 3, "Fast food", "Fried rice"),
    ("Pasta (Creamy)", "🍝", "1 plate", 540, 18, 62, 24, 4, "Fast food", "Pasta"),
    ("Sausage", "🌭", "2 links", 250, 12, 2, 22, 0, "Fast food", "Sausage"),
    ("Doughnut", "🍩", "1 piece", 250, 3, 31, 13, 1, "Fast food", "Doughnut"),
    ("Chicken Patties", "🥟", "1 piece", 230, 8, 22, 13, 1, "Fast food", None),
]


API = "https://en.wikipedia.org/w/api.php"

# Built-in "Everyday" foods (defined in core/nutrition.FOODS) -> Wikipedia title
EVERYDAY_TITLES = {
    "Oatmeal": "Oatmeal", "Greek Yogurt": "Strained yogurt", "Banana": "Banana",
    "Apple": "Apple", "Scrambled Eggs": "Scrambled eggs", "Avocado Toast": "Avocado toast",
    "Grilled Chicken Breast": "Chicken as food", "Salmon Fillet": "Salmon as food",
    "Brown Rice": "Brown rice", "Quinoa": "Quinoa", "Caesar Salad": "Caesar salad",
    "Mixed Green Salad": "Salad", "Spaghetti Bolognese": "Bolognese sauce",
    "Margherita Pizza": "Pizza Margherita", "Cheeseburger": "Cheeseburger",
    "Sushi Roll": "Sushi", "Caesar Wrap": "Wrap (food)", "Chicken Stir-fry": "Stir frying",
    "Beef Steak": "Beefsteak", "Tofu Bowl": "Tofu", "Protein Shake": "Milkshake",
    "Almonds": "Almond", "Peanut Butter": "Peanut butter", "Dark Chocolate": "Chocolate",
    "Strawberries": "Strawberry", "Blueberries": "Blueberry", "Orange": "Orange (fruit)",
    "Coffee (black)": "Coffee", "Latte": "Latte", "Croissant": "Croissant",
    "Pancakes": "Pancake", "French Fries": "French fries", "Ice Cream": "Ice cream",
    "Hummus": "Hummus", "Lentil Soup": "Lentil soup", "Cottage Cheese": "Cottage cheese",
    "Whole Wheat Bread": "Whole wheat bread", "Boiled Egg": "Boiled egg",
    "Mango": "Mango", "Sweet Potato": "Sweet potato",
}


def fetch_batch(titles, session):
    """Fetch thumbnails for up to ~50 titles in one request, resolving redirects."""
    params = {"action": "query", "format": "json", "prop": "pageimages",
              "piprop": "thumbnail", "pithumbsize": 320, "redirects": 1,
              "titles": "|".join(titles)}
    try:
        r = session.get(API, params=params, headers=HEADERS, timeout=30)
        data = (r.json() or {}).get("query", {})
    except Exception:
        time.sleep(2)  # transient rate-limit / non-JSON response — back off, skip chunk
        return {t: "" for t in titles}
    alias = {}
    for n in data.get("normalized", []):
        alias[n["from"]] = n["to"]
    for rd in data.get("redirects", []):
        alias[rd["from"]] = rd["to"]
    title2thumb = {}
    for _, page in (data.get("pages") or {}).items():
        src = (page.get("thumbnail") or {}).get("source")
        if src:
            title2thumb[page["title"]] = src

    def resolve(t):
        seen = set()
        while t in alias and t not in seen:
            seen.add(t)
            t = alias[t]
        return t

    return {t: title2thumb.get(resolve(t), "") for t in titles}


_BAD = ("icon", "logo", "map", "flag", "coat_of_arms", "symbol", "stamp", ".svg",
        "label", "packaging", "bottle", "menu", "sign", "poster", "diagram")
_STOP = {"with", "food", "dish", "the", "and", "fresh", "style", "curry"}
# manual Commons search overrides for dishes whose name doesn't match filenames well
MANUAL = {
    "Beef Curry": "beef curry",
    "Chicken Roast": "roast chicken",
    "Chicken Curry": "chicken curry",
    "Mutton Curry": "mutton curry",
    "Beef Tehari": "tehari",
    "Beef Chui Jhal": "beef bhuna",
    "Gorur Kolija Bhuna (Liver)": "beef liver fry",
    "Egg Curry (Dim Bhuna)": "egg curry",
    "Koi Macher Curry": "koi fish curry",
    "Lau Chingri": "prawn bottle gourd",
    "Aloo Bhorta": "aloo bharta",
    "Begun Bhorta": "baingan bharta",
    "Mixed Vegetables (Shobji)": "mixed vegetable curry",
    "Cholar Dal": "cholar dal",
    "Mashkalai Dal": "biulir dal",
    "Dimer Chop (Egg chop)": "egg chop",
    "Dal Puri": "dal puri",
    "Piyaju": "piyaju lentil fritter",
    "Nakshi Pitha": "nakshi pitha",
    "Wood Apple (Bel)": "bael fruit",
    "Zinger Burger": "fried chicken burger",
    "Chicken Patties": "chicken patties",
}


def clean_query(name):
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", name)).strip()


def valid_image(session, url):
    """True only if the URL returns a live image (drops 404s / non-image / Openverse)."""
    if not url or "upload.wikimedia.org" not in url:
        return False
    try:
        r = session.get(url, headers=HEADERS, timeout=15, stream=True)
        ok = r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/")
        r.close()
        return ok
    except Exception:
        return False


def commons_candidates(session, query):
    try:
        r = session.get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": 12,
            "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 320,
        }, headers=HEADERS, timeout=20)
        pages = (r.json().get("query") or {}).get("pages") or {}
        out = []
        for p in sorted(pages.values(), key=lambda x: x.get("index", 999)):
            ii = (p.get("imageinfo") or [{}])[0]
            out.append((p.get("title", ""), ii.get("thumburl", ""), ii.get("mime", "")))
        return out
    except Exception:
        return []


def commons_best(session, name):
    """A Commons photo for the dish. Commons thumbnails are direct upload.wikimedia.org
    links, so they render without extra validation. For curated (MANUAL) dishes we trust
    the precise query and take the top usable result; otherwise we require the filename
    to be relevant to the dish name (avoids wrong matches)."""
    is_manual = name in MANUAL
    base = MANUAL.get(name, clean_query(name))
    tokens = [w for w in re.findall(r"[a-z]+", base.lower()) if len(w) >= 4 and w not in _STOP]
    for q in (base, f"{base} food"):
        for title, thumb, mime in commons_candidates(session, q):
            tl = title.lower()
            if not thumb or mime == "image/svg+xml" or any(b in tl for b in _BAD):
                continue
            if is_manual or (any(tok in tl for tok in tokens) if tokens else True):
                return thumb
        time.sleep(0.12)
    return ""


def find_image(session, name, cat, wiki_thumb):
    """Wikipedia lead image (trusted; direct Wikimedia links render reliably) else a
    filename-matched + validated Commons photo, else emoji. No Openverse (it caused
    the wrong / non-rendering images)."""
    if name not in MANUAL and wiki_thumb:
        return wiki_thumb, "wiki"
    img = commons_best(session, name)   # validates only the chosen Commons candidate
    if img:
        return img, "commons"
    return "", "none"


def main():
    session = requests.Session()
    titles = sorted({t for *_, t in CATALOG if t})
    thumbs = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        thumbs.update(fetch_batch(chunk, session))
        time.sleep(0.5)

    items = []
    for (name, emoji, unit, kcal, p, c, f, fib, cat, title) in CATALOG:
        wiki_thumb = thumbs.get(title, "") if title else ""
        img, src = find_image(session, name, cat, wiki_thumb)
        items.append({"name": name, "emoji": emoji, "unit": unit, "calories": kcal,
                      "protein": p, "carbs": c, "fat": f, "fiber": fib,
                      "cat": cat, "image": img})
        tag = {"wiki": "[wiki]", "commons": "[cmns]", "openverse": "[ovrs]", "none": "[emo ]"}[src]
        print(f"  {tag} {name}")

    with open("core/foods_bd.py", "w", encoding="utf-8") as fh:
        fh.write('"""Bangladeshi dishes, BD fruits and global savory foods.\n')
        fh.write("Auto-generated by _build_bd.py — image URLs are Wikimedia thumbnails.\n")
        fh.write('Each item: name, emoji, unit, calories, protein, carbs, fat, fiber, cat, image."""\n\n')
        fh.write("FOODS_BD = [\n")
        for it in items:
            fh.write("    " + json.dumps(it, ensure_ascii=False) + ",\n")
        fh.write("]\n")
    n_img = sum(1 for it in items if it["image"])
    print(f"\nWrote core/foods_bd.py — {len(items)} items, {n_img} with images.")

    # ---- everyday built-in foods image map ----
    ev_titles = sorted(set(EVERYDAY_TITLES.values()))
    ev_thumbs = {}
    for i in range(0, len(ev_titles), 40):
        ev_thumbs.update(fetch_batch(ev_titles[i:i + 40], session))
        time.sleep(0.5)
    ev_map = {}
    for name, title in EVERYDAY_TITLES.items():
        url = ev_thumbs.get(title, "")     # trusted Wikipedia lead images
        if url:
            ev_map[name] = url
            print("  [img] " + name)
        else:
            print("  [emo] " + name)

    # Don't overwrite a good map with a rate-limited (mostly empty) one.
    if len(ev_map) >= int(0.6 * len(EVERYDAY_TITLES)):
        with open("core/foods_img.py", "w", encoding="utf-8") as fh:
            fh.write('"""Image URLs for built-in everyday foods. Auto-generated by _build_bd.py."""\n\n')
            fh.write("EVERYDAY_IMAGES = {\n")
            for name, url in ev_map.items():
                fh.write(f"    {json.dumps(name, ensure_ascii=False)}: {json.dumps(url, ensure_ascii=False)},\n")
            fh.write("}\n")
        print(f"\nWrote core/foods_img.py — {len(ev_map)}/{len(EVERYDAY_TITLES)} everyday foods with images.")
    else:
        print(f"\nSkipped core/foods_img.py — only {len(ev_map)} resolved (likely rate-limited); kept existing.")


if __name__ == "__main__":
    main()
