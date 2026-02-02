import sqlite3
import datetime
import logging

DB_NAME = "bot_data.db"
logger = logging.getLogger(__name__)

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS published (
                id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database init error: {e}")

def is_published(pin_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM published WHERE id = ?", (pin_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking published status: {e}")
        return False

def mark_as_published(pin_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO published (id) VALUES (?)", (pin_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error marking as published: {e}")
