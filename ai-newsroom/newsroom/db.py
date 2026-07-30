import sqlite3
import time
from pathlib import Path

from .paths import DB_PATH, APP_DIR

MIGRATIONS_DIR = APP_DIR / "migrations"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def run_migrations():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        success INTEGER,
        duration_ms INTEGER)""")
    done = {r["version"] for r in conn.execute(
        "SELECT version FROM schema_migrations WHERE success=1")}
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        t0 = time.time()
        try:
            with conn:  # એક TRANSACTION — ફેલ થાય તો બધું પાછું
                conn.executescript(path.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations(version, success, duration_ms) VALUES(?,?,?)",
                    (path.name, 1, int((time.time() - t0) * 1000)))
        except Exception:
            conn.close()
            raise
    conn.close()


def query(sql: str, params=()) -> list[dict]:
    conn = get_db()
    try:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        return rows
    finally:
        conn.close()


def execute(sql: str, params=()) -> int:
    conn = get_db()
    try:
        with conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid
    finally:
        conn.close()


def bump_stat(date: str, column: str, amount: int = 1):
    conn = get_db()
    try:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO daily_stats(date) VALUES(?)", (date,))
            conn.execute(
                f"UPDATE daily_stats SET {column} = {column} + ? WHERE date = ?",
                (amount, date))
    finally:
        conn.close()
