import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("CSR_DB_PATH", "data/context_switch_radar.db"))
_DB_READY = False


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    global _DB_READY
    _ensure_parent(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                task_key TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS climate_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT NOT NULL,
                memory_date TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                city TEXT NOT NULL DEFAULT '',
                climate_tag TEXT NOT NULL DEFAULT '',
                feeling TEXT NOT NULL DEFAULT '',
                temp_c REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    _DB_READY = True


@contextmanager
def get_conn():
    if not _DB_READY:
        init_db()
    _ensure_parent(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
