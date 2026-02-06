# config.py
import os
from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Env var {name} must be an integer, got {value!r}")


def _get_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# Токен — обязателен
BOT_TOKEN = _get_str("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")

# Канал (может быть числом или @username)
CHANNEL_ID = _get_str("CHANNEL_ID")
if not CHANNEL_ID:
    raise RuntimeError("CHANNEL_ID is not set in environment")

# Админ (для уведомлений)
ADMIN_ID = _get_int("ADMIN_ID")

# Порт Flask / Render
PORT = _get_int("PORT", 10000)

# Pinterest
PINTEREST_SEARCH_URL = _get_str(
    "PINTEREST_SEARCH_URL",
    "https://www.pinterest.com/search/pins/?q=toned%20women%20beach%20style&rs=typed",
)

# Интервал публикаций (минуты)
PUBLISH_DELAY_MINUTES = int(os.getenv("PUBLISH_DELAY_MINUTES", "20"))
