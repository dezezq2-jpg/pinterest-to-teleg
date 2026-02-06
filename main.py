# main.py
import asyncio
import logging
import random
import signal
import sys
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

import config
from database import init_db, is_published, mark_as_published
from parser import get_pinterest_images
from publisher import publish_photo
import requests  # нужен только для keep‑alive

# ----------------------------------------------------------------------
# 1️⃣ Logging
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 2️⃣ Flask (для health‑check, нужен keep‑alive)
# ----------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Pinterest Bot is running! ✅"

@app.route("/health")
def health():
    return {"status": "ok", "bot": "running"}

# ----------------------------------------------------------------------
# 3️⃣ Bot & Scheduler (глобальные переменные)
# ----------------------------------------------------------------------
bot: Bot | None = None
scheduler: BackgroundScheduler | None = None

# ----------------------------------------------------------------------
# 4️⃣ Асинхронная работа (публикация)
# ----------------------------------------------------------------------
async def async_publish_job() -> None:
    """Выполняется каждый запуск планировщика."""
    logger.info("▶️ Запуск задачи публикации")

    if not config.BOT_TOKEN or not config.CHANNEL_ID:
        logger.error("BOT_TOKEN или CHANNEL_ID не заданы!")
        return

    # 1️⃣ Получаем список пинов
    items = await get_pinterest_images(config.PINTEREST_SEARCH_URL)
    if not items:
        logger.info("🔍 Пинов не найдено")
        return

    # 2️⃣ Выбираем непубликовавшийся
    random.shuffle(items)
    candidate = next((i for i in items if not is_published(i["id"])), None)

    if not candidate:
        logger.info("✅ Все найденные пины уже опубликованы")
        return

    # 3️⃣ Публикуем
    logger.info(f"Attempting to publish: {candidate['id']}")
    success = await publish_photo(bot, candidate["url"])

    if success:
        mark_as_published(candidate["id"])
        logger.info(f"✅ Пин {candidate['id']} опубликован")
    else:
        logger.warning(f"❗ Пин {candidate['id']} НЕ опубликован (будет повторена попытка позже)")

# ----------------------------------------------------------------------
# 5️⃣ Синхронная обёртка для планировщика
# ----------------------------------------------------------------------
def job_wrapper() -> None:
    """
    BackgroundScheduler (синхронный) не умеет выполнять корутины.
    Поэтому создаём короткий event‑loop, в котором вызываем async‑функцию.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_publish_job())
    except Exception as exc:
        logger.error(f"Ошибка в job_wrapper: {exc}", exc_info=True)
    finally:
        # Очень важно «чисто» убрать текущий loop, иначе при следующем запуске
        # asyncio.get_event_loop() может вернуть уже закрытый цикл.
        asyncio.set_event_loop(None)

# ----------------------------------------------------------------------
# 6️⃣ Keep‑alive (пинг самого себя) – синхронно, проще использовать requests
# ----------------------------------------------------------------------
def keep_alive() -> None:
    try:
        service_url = "https://pinterest-to-teleg.onrender.com"
        requests.get(f"{service_url}/health", timeout=5)
        logger.info("💓 Keep‑alive ping sent")
    except Exception as exc:
        logger.warning(f"💓 Keep‑alive ping failed: {exc}")

# ----------------------------------------------------------------------
# 7️⃣ Инициализация бота и планировщика
# ----------------------------------------------------------------------
def init_bot_and_scheduler() -> None:
    global bot, scheduler

    if bot is not None:
        logger.warning("Bot уже инициализирован – повторный вызов игнорируется")
        return

    logger.info("🚀 Инициализация бота и планировщика")
    init_db()                     # создаём таблицу, если её ещё нет
    bot = Bot(token=config.BOT_TOKEN)

    scheduler = BackgroundScheduler()

    # Публикация каждые PUBLISH_DELAY_MINUTES минут
    scheduler.add_job(
        job_wrapper,
        "interval",
        minutes=config.PUBLISH_DELAY_MINUTES,
        next_run_time=datetime.now() + timedelta(seconds=10),
        id="publish_job",
        misfire_grace_time=60,
    )

    # Keep‑alive каждые 3 минуты (можно увеличить)
    scheduler.add_job(
        keep_alive,
        "interval",
        minutes=3,
        next_run_time=datetime.now() + timedelta(seconds=30),
        id="keepalive_job",
        misfire_grace_time=30,
    )

    scheduler.start()
    logger.info(f"✅ Планировщик запущен (интервал {config.PUBLISH_DELAY_MINUTES} мин)")

# ----------------------------------------------------------------------
# 8️⃣ Graceful shutdown (чистое завершение при SIGINT/SIGTERM)
# ----------------------------------------------------------------------
def _shutdown(*_):
    logger.info("🛑 Получен сигнал завершения – делаем graceful‑shutdown")
    if scheduler:
        scheduler.shutdown(wait=False)
    if bot:
        # закрываем aiohttp‑сессию внутри Bot
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(bot.session.close())
        except RuntimeError:
            # если нет запущенного цикла – просто создаём временный
            asyncio.run(bot.session.close())
    logger.info("✅ Выключение завершено")
    sys.exit(0)


# регистрируем обработчики сигналов (Render посылает SIGTERM при рестарте)
signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

# ----------------------------------------------------------------------
# 9️⃣ Запуск (для локального `python main.py` и для gunicorn)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # локальный запуск
    init_bot_and_scheduler()
    port = int(config.PORT) if config.PORT else 10000
    app.run(host="0.0.0.0", port=port, debug=False)
else:
    # когда процесс стартует через gunicorn – сразу поднимаем бота и планировщик
    init_bot_and_scheduler()
