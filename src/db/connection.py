import sqlite3
from pathlib import Path

DB_PATH = Path("data/monitor.db")
SCHEMA_PATH = Path("src/db/schema.sql")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
        conn.commit()
        return conn