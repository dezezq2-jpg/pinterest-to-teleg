# config.py
"""
Central place for all environment‑variables used by the bot.

*   All variables are loaded with `python‑dotenv` (so you can keep them
    in a `.env` file for local development).
*   Required variables raise a clear error if they are missing.
*   `CHANNEL_ID` и `ADMIN_ID` ‑ всегда **int**, если передано чистое число,
    иначе – оставляем строку (для имени/username) и приводим к `int`
    только в нужный момент.
"""

import os
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# 1️⃣ Load .env (if it exists) – works also on Render, where переменные
#    уже заданы в UI.
# ----------------------------------------------------------------------
load_dotenv()


# ----------------------------------------------------------------------
# 2️⃣ Helper functions
# ----------------------------------------------------------------------
def _required(var_name: str) -> str:
    """
    Возвращает значение переменной, бросая RuntimeError,
    если переменная не найдена.
    """
    value = os.getenv(var_name)
    if value is None or value == "":
        raise RuntimeError(f"❌ {var_name} is not set in the environment")
    return value.strip()


def _optional_int(var_name: str, default: int | None = None) -> int | None:
    """
    Возвращает переменную как int, если она присутствует и является числом.
    Если переменной нет – возвращает `default`.
    """
    raw = os.getenv(var_name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        # Не число – просто игнорируем (например, ADMIN_ID, если задали как строку)
        return default


# ----------------------------------------------------------------------
# 3️⃣ Обязательные настройки
# ----------------------------------------------------------------------
BOT_TOKEN: str = _required("BOT_TOKEN")          # токен, полученный у BotFather
_raw_channel = _required("CHANNEL_ID")           # может быть числом или @username


# ----------------------------------------------------------------------
# 4️⃣ CHANNEL_ID – переводим в int, если это чистый идентификатор
# ----------------------------------------------------------------------
try:
    # Если переменная выглядит как «-1001234567890» (или «1001234567890»)
    CHANNEL_ID: int = int(_raw_channel.lstrip().replace(" ", ""))
except ValueError:
    # Не число – считаем, что это имя/username (например, "my_channel")
    # Оставляем как строку без символа «@», чтобы _resolve_channel_id
    # мог при необходимости вызвать bot.get_chat().
    CHANNEL_ID = _raw_channel.lstrip("@").strip()


# ----------------------------------------------------------------------
# 5️⃣ Необязательные настройки
# ----------------------------------------------------------------------
ADMIN_ID: int | None = _optional_int("ADMIN_ID")  # ваш личный Telegram‑ID (для уведомлений)

PORT: int = int(os.getenv("PORT", "10000"))      # порт, который слушает Flask (Render требует 10000)

PINTEREST_SEARCH_URL: str = os.getenv(
    "PINTEREST_SEARCH_URL",
    "https://www.pinterest.com/search/pins/?q=toned%20women%20beach%20style&rs=typed",
)

# Интервал публикаций в минутах (по‑умолчанию 20)
PUBLISH_DELAY_MINUTES: int = int(os.getenv("PUBLISH_DELAY_MINUTES", "20"))


# ----------------------------------------------------------------------
# 6️⃣ Краткое представление (полезно при запуске скриптов)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # При запуске `python config.py` выведем все текущие настройки.
    print("=== Bot configuration ===")
    print(f"BOT_TOKEN            : {'*' * (len(BOT_TOKEN) - 6) + BOT_TOKEN[-6:]}")
    print(f"CHANNEL_ID (int)     : {CHANNEL_ID}")
    print(f"ADMIN_ID             : {ADMIN_ID}")
    print(f"PORT                 : {PORT}")
    print(f"PINTEREST_SEARCH_URL : {PINTEREST_SEARCH_URL}")
    print(f"PUBLISH_DELAY_MINUTES: {PUBLISH_DELAY_MINUTES}")
