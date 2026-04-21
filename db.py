import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "cafeteria.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema)
        _apply_migrations(conn)


def _apply_migrations(conn):
    activity_columns = {row["name"] for row in conn.execute("PRAGMA table_info(Activity)").fetchall()}
    if "Order_id" not in activity_columns:
        conn.execute("ALTER TABLE Activity ADD COLUMN Order_id INTEGER")
    conn.commit()


def fetch_all(query, params=()):
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


def fetch_one(query, params=()):
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
    return row


def execute(query, params=()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        conn.commit()
    return cur.lastrowid


def execute_many(query, seq):
    with get_connection() as conn:
        conn.executemany(query, seq)
        conn.commit()
