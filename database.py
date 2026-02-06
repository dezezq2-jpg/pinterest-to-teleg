# database.py
import sqlite3
import logging

DB_NAME = "bot_data.db"
logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Создаёт таблицу `published`, если её ещё нет.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
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
    """
    Возвращает True, если данный pin уже был опубликован.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM published WHERE id = ?", (pin_id,))
            result = cur.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Error checking published status: {e}")
        return False


def mark_as_published(pin_id: str) -> None:
    """
    Записывает pin_id в базу, чтобы не публиковать повторно.
    """
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO published (id) VALUES (?)", (pin_id,)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error marking as published: {e}")
