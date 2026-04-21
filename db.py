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
    
    purchase_columns = {row["name"] for row in conn.execute("PRAGMA table_info(Purchase)").fetchall()}
    if "Purchase_type" not in purchase_columns:
        conn.execute("ALTER TABLE Purchase ADD COLUMN Purchase_type TEXT NOT NULL DEFAULT 'raw'")

    order_columns = {row["name"] for row in conn.execute("PRAGMA table_info(Orders)").fetchall()}
    if "Delivery_date" not in order_columns:
        conn.execute("ALTER TABLE Orders ADD COLUMN Delivery_date TEXT")
        conn.execute("UPDATE Orders SET Delivery_date = Date WHERE Delivery_date IS NULL")
    if "Delivery_window" not in order_columns:
        conn.execute("ALTER TABLE Orders ADD COLUMN Delivery_window TEXT NOT NULL DEFAULT 'morning'")
    if "Status" not in order_columns:
        conn.execute("ALTER TABLE Orders ADD COLUMN Status TEXT NOT NULL DEFAULT 'pending'")
    conn.execute("UPDATE Orders SET Delivery_date = Date WHERE Delivery_date IS NULL OR Delivery_date = ''")
    conn.execute("UPDATE Orders SET Delivery_window = 'morning' WHERE Delivery_window IS NULL OR Delivery_window = ''")
    conn.execute("UPDATE Orders SET Status = 'pending' WHERE Status IS NULL OR Status = ''")
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
