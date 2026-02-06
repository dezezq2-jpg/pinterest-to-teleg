# database.py
import sqlite3
import logging
from contextlib import closing

DB_NAME = "bot_data.db"
logger = logging.getLogger(__name__)


def _connect():
    return sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)


def init_db():
    try:
        with closing(_connect()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS published (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Database init error: {e}")


def is_published(pin_id: str) -> bool:
    try:
        with closing(_connect()) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM published WHERE id = ?", (pin_id,))
            return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking published status: {e}")
        return False


def mark_as_published(pin_id: str):
    try:
        with closing(_connect()) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT OR IGNORE INTO published (id) VALUES (?)", (pin_id,)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error marking as published: {e}")
