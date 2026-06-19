"""
Local-first persistence for NutriSnap.

Everything is stored on-device in a single SQLite file (data/nutrisnap.db).
No accounts, no servers — one local profile. All reads/writes go through here.
"""
from __future__ import annotations

import os
import json
import sqlite3
from datetime import date, datetime, timedelta

import streamlit as st

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "nutrisnap.db")


@st.cache_resource(show_spinner=False)
def _conn() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT, sex TEXT, age INTEGER,
            height_cm REAL, weight_kg REAL, activity TEXT, goal TEXT,
            target_weight_kg REAL, rate_kg_wk REAL,
            calorie_goal INTEGER, protein_g INTEGER, carbs_g INTEGER, fat_g INTEGER,
            water_goal_ml INTEGER, onboarded INTEGER DEFAULT 0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT, meal TEXT, name TEXT, emoji TEXT, image TEXT DEFAULT '',
            qty REAL DEFAULT 1, unit TEXT DEFAULT 'serving',
            calories REAL, protein REAL, carbs REAL, fat REAL, fiber REAL,
            source TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT UNIQUE, weight_kg REAL, note TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS water_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT, amount_ml INTEGER, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT, content TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS achievements (
            code TEXT PRIMARY KEY, unlocked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS custom_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, emoji TEXT, image TEXT DEFAULT '', unit TEXT DEFAULT 'serving',
            calories REAL, protein REAL, carbs REAL, fat REAL, fiber REAL, created_at TEXT
        );
        """
    )
    # Lightweight migration for DBs created before the image column existed.
    cols = {r["name"] for r in cur.execute("PRAGMA table_info(food_log)").fetchall()}
    if "image" not in cols:
        cur.execute("ALTER TABLE food_log ADD COLUMN image TEXT DEFAULT ''")
    conn.commit()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today() -> str:
    return date.today().isoformat()


# ----------------------------- meta / settings ------------------------------
def get_meta(key: str, default=None):
    row = _conn().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except (json.JSONDecodeError, TypeError):
        return row["value"]


def set_meta(key: str, value) -> None:
    _conn().execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value)),
    )
    _conn().commit()


# --------------------------------- profile ----------------------------------
def get_profile() -> dict | None:
    row = _conn().execute("SELECT * FROM profile WHERE id=1").fetchone()
    return dict(row) if row else None


def save_profile(data: dict) -> None:
    data = {**data, "id": 1, "created_at": data.get("created_at") or _now()}
    cols = ", ".join(data.keys())
    ph = ", ".join("?" for _ in data)
    updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "id")
    _conn().execute(
        f"INSERT INTO profile({cols}) VALUES({ph}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        tuple(data.values()),
    )
    _conn().commit()


def is_onboarded() -> bool:
    p = get_profile()
    return bool(p and p.get("onboarded"))


# -------------------------------- food log ----------------------------------
def add_food(meal: str, item: dict, log_date: str | None = None) -> None:
    """Add a food entry. Macros are stored PER UNIT; `qty` is the count.
    Re-adding an identical food (same meal/name/unit/per-unit calories) on the same
    day just bumps its quantity instead of creating a duplicate row."""
    log_date = log_date or today()
    name = item.get("name", "Food")
    unit = item.get("unit", "serving")
    cals = float(item.get("calories", 0))
    qty = float(item.get("qty", 1) or 1)

    existing = _conn().execute(
        """SELECT id FROM food_log
           WHERE log_date=? AND meal=? AND name=? AND unit=? AND calories=?""",
        (log_date, meal, name, unit, cals),
    ).fetchone()
    if existing:
        _conn().execute("UPDATE food_log SET qty=qty+? WHERE id=?", (qty, existing["id"]))
        _conn().commit()
        return

    _conn().execute(
        """INSERT INTO food_log
           (log_date, meal, name, emoji, image, qty, unit, calories, protein, carbs, fat, fiber, source, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            log_date, meal, name, item.get("emoji", "🍽️"), item.get("image", "") or "",
            qty, unit, cals,
            float(item.get("protein", 0)), float(item.get("carbs", 0)),
            float(item.get("fat", 0)), float(item.get("fiber", 0)),
            item.get("source", "manual"), _now(),
        ),
    )
    _conn().commit()


def add_custom_food(item: dict) -> None:
    """Save (or update) a user-created food so it's reusable in search. Per-unit macros."""
    _conn().execute(
        """INSERT INTO custom_foods
           (name, emoji, image, unit, calories, protein, carbs, fat, fiber, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(name) DO UPDATE SET
             emoji=excluded.emoji, image=excluded.image, unit=excluded.unit,
             calories=excluded.calories, protein=excluded.protein, carbs=excluded.carbs,
             fat=excluded.fat, fiber=excluded.fiber""",
        (item.get("name", "Custom food"), item.get("emoji", "🍽️"), item.get("image", "") or "",
         item.get("unit", "serving"), float(item.get("calories", 0)), float(item.get("protein", 0)),
         float(item.get("carbs", 0)), float(item.get("fat", 0)), float(item.get("fiber", 0)), _now()),
    )
    _conn().commit()


def get_custom_foods() -> list[dict]:
    rows = _conn().execute(
        "SELECT name, emoji, image, unit, calories, protein, carbs, fat, fiber "
        "FROM custom_foods ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_custom_food(name: str) -> None:
    _conn().execute("DELETE FROM custom_foods WHERE name=?", (name,))
    _conn().commit()


def adjust_food_qty(food_id: int, delta: float) -> None:
    """Increase/decrease an entry's quantity. Removes the row if it drops to 0."""
    row = _conn().execute("SELECT qty FROM food_log WHERE id=?", (food_id,)).fetchone()
    if not row:
        return
    new_qty = (row["qty"] or 1) + delta
    if new_qty <= 0:
        _conn().execute("DELETE FROM food_log WHERE id=?", (food_id,))
    else:
        _conn().execute("UPDATE food_log SET qty=? WHERE id=?", (new_qty, food_id))
    _conn().commit()


def get_foods(log_date: str | None = None) -> list[dict]:
    log_date = log_date or today()
    rows = _conn().execute(
        "SELECT * FROM food_log WHERE log_date=? ORDER BY id", (log_date,)
    ).fetchall()
    return [dict(r) for r in rows]


def delete_food(food_id: int) -> None:
    _conn().execute("DELETE FROM food_log WHERE id=?", (food_id,))
    _conn().commit()


def day_totals(log_date: str | None = None) -> dict:
    log_date = log_date or today()
    row = _conn().execute(
        """SELECT COALESCE(SUM(calories*qty),0) c, COALESCE(SUM(protein*qty),0) p,
                  COALESCE(SUM(carbs*qty),0) cb, COALESCE(SUM(fat*qty),0) f,
                  COALESCE(SUM(fiber*qty),0) fb, COUNT(*) n
           FROM food_log WHERE log_date=?""",
        (log_date,),
    ).fetchone()
    return {"calories": row["c"], "protein": row["p"], "carbs": row["cb"],
            "fat": row["f"], "fiber": row["fb"], "items": row["n"]}


def meal_totals(log_date: str | None = None) -> dict:
    log_date = log_date or today()
    rows = _conn().execute(
        "SELECT meal, COALESCE(SUM(calories*qty),0) c FROM food_log WHERE log_date=? GROUP BY meal",
        (log_date,),
    ).fetchall()
    return {r["meal"]: r["c"] for r in rows}


def range_totals(days: int = 7) -> list[dict]:
    """Per-day calorie + macro totals for the last `days` days (oldest first)."""
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = _conn().execute(
        """SELECT log_date,
                  COALESCE(SUM(calories*qty),0) calories, COALESCE(SUM(protein*qty),0) protein,
                  COALESCE(SUM(carbs*qty),0) carbs, COALESCE(SUM(fat*qty),0) fat,
                  COALESCE(SUM(fiber*qty),0) fiber
           FROM food_log WHERE log_date>=? GROUP BY log_date""",
        (start,),
    ).fetchall()
    by_date = {r["log_date"]: dict(r) for r in rows}
    out = []
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        out.append(by_date.get(d, {"log_date": d, "calories": 0, "protein": 0,
                                   "carbs": 0, "fat": 0, "fiber": 0}))
    return out


def favorites(limit: int = 8) -> list[dict]:
    rows = _conn().execute(
        """SELECT name, emoji, ROUND(AVG(calories)) calories, ROUND(AVG(protein)) protein,
                  ROUND(AVG(carbs)) carbs, ROUND(AVG(fat)) fat, ROUND(AVG(fiber)) fiber,
                  COUNT(*) freq
           FROM food_log GROUP BY name ORDER BY freq DESC, MAX(id) DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def recent_foods(limit: int = 10) -> list[dict]:
    rows = _conn().execute(
        "SELECT name, emoji, calories, protein, carbs, fat, fiber FROM food_log "
        "GROUP BY name ORDER BY MAX(id) DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def logged_dates() -> set[str]:
    rows = _conn().execute("SELECT DISTINCT log_date FROM food_log").fetchall()
    return {r["log_date"] for r in rows}


# -------------------------------- weight log ---------------------------------
def add_weight(weight_kg: float, log_date: str | None = None, note: str = "") -> None:
    log_date = log_date or today()
    _conn().execute(
        "INSERT INTO weight_log(log_date, weight_kg, note, created_at) VALUES(?,?,?,?) "
        "ON CONFLICT(log_date) DO UPDATE SET weight_kg=excluded.weight_kg, note=excluded.note",
        (log_date, weight_kg, note, _now()),
    )
    # keep profile's current weight in sync with the latest entry
    latest = _conn().execute(
        "SELECT weight_kg FROM weight_log ORDER BY log_date DESC LIMIT 1"
    ).fetchone()
    if latest:
        _conn().execute("UPDATE profile SET weight_kg=? WHERE id=1", (latest["weight_kg"],))
    _conn().commit()


def get_weights() -> list[dict]:
    rows = _conn().execute(
        "SELECT log_date, weight_kg, note FROM weight_log ORDER BY log_date"
    ).fetchall()
    return [dict(r) for r in rows]


# -------------------------------- water log ----------------------------------
def add_water(amount_ml: int, log_date: str | None = None) -> None:
    _conn().execute(
        "INSERT INTO water_log(log_date, amount_ml, created_at) VALUES(?,?,?)",
        (log_date or today(), amount_ml, _now()),
    )
    _conn().commit()


def water_today(log_date: str | None = None) -> int:
    row = _conn().execute(
        "SELECT COALESCE(SUM(amount_ml),0) t FROM water_log WHERE log_date=?",
        (log_date or today(),),
    ).fetchone()
    return int(row["t"])


def water_range(days: int = 7) -> list[dict]:
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = _conn().execute(
        "SELECT log_date, COALESCE(SUM(amount_ml),0) amount_ml FROM water_log "
        "WHERE log_date>=? GROUP BY log_date",
        (start,),
    ).fetchall()
    by = {r["log_date"]: r["amount_ml"] for r in rows}
    return [{"log_date": (date.today() - timedelta(days=days - 1 - i)).isoformat(),
             "amount_ml": by.get((date.today() - timedelta(days=days - 1 - i)).isoformat(), 0)}
            for i in range(days)]


def reset_water_today(log_date: str | None = None) -> None:
    _conn().execute("DELETE FROM water_log WHERE log_date=?", (log_date or today(),))
    _conn().commit()


# ----------------------------------- chat ------------------------------------
def add_chat(role: str, content: str) -> None:
    _conn().execute(
        "INSERT INTO chat(role, content, created_at) VALUES(?,?,?)",
        (role, content, _now()),
    )
    _conn().commit()


def get_chat() -> list[dict]:
    rows = _conn().execute("SELECT role, content FROM chat ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def clear_chat() -> None:
    _conn().execute("DELETE FROM chat")
    _conn().commit()


# ------------------------------- achievements --------------------------------
def unlock(code: str) -> bool:
    """Returns True if this is a *new* unlock."""
    exists = _conn().execute("SELECT 1 FROM achievements WHERE code=?", (code,)).fetchone()
    if exists:
        return False
    _conn().execute("INSERT INTO achievements(code, unlocked_at) VALUES(?,?)", (code, _now()))
    _conn().commit()
    return True


def unlocked_codes() -> set[str]:
    rows = _conn().execute("SELECT code FROM achievements").fetchall()
    return {r["code"] for r in rows}


# ----------------------- meal templates / quick meals ------------------------
def get_meal_templates() -> list[dict]:
    return get_meta("meal_templates", []) or []


def save_meal_template(name: str, items: list[dict]) -> None:
    name = (name or "Meal").strip()
    tpls = [t for t in get_meal_templates() if t.get("name", "").lower() != name.lower()]
    tpls.append({"name": name, "items": items, "created_at": _now()})
    set_meta("meal_templates", tpls)


def delete_meal_template(name: str) -> None:
    set_meta("meal_templates", [t for t in get_meal_templates() if t.get("name") != name])


# ------------------------------ recent searches ------------------------------
def get_recent_searches() -> list[str]:
    return get_meta("recent_searches", []) or []


def add_recent_search(q: str) -> None:
    q = (q or "").strip()
    if len(q) < 2:
        return
    lst = [s for s in get_recent_searches() if s.lower() != q.lower()]
    lst.insert(0, q)
    set_meta("recent_searches", lst[:6])


# ----------------------------- export / reset --------------------------------
def export_all() -> dict:
    c = _conn()
    return {
        "exported_at": _now(),
        "profile": get_profile(),
        "food_log": [dict(r) for r in c.execute("SELECT * FROM food_log").fetchall()],
        "weight_log": get_weights(),
        "water_log": [dict(r) for r in c.execute("SELECT * FROM water_log").fetchall()],
        "achievements": [dict(r) for r in c.execute("SELECT * FROM achievements").fetchall()],
    }


def wipe_logs() -> None:
    c = _conn()
    for t in ("food_log", "weight_log", "water_log", "chat", "achievements"):
        c.execute(f"DELETE FROM {t}")
    c.commit()


def wipe_everything() -> None:
    c = _conn()
    for t in ("food_log", "weight_log", "water_log", "chat", "achievements", "profile", "meta"):
        c.execute(f"DELETE FROM {t}")
    c.commit()
