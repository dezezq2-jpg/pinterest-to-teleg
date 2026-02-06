# main.py
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta

from aiohttp import ClientSession
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask

import config
from database import init_db, is_published, mark_as_published
from parser import get_pinterest_images
from publisher import publish_photo

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Flask (health‑checks)
# -------------------------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Pinterest Bot is running ✅"

@app.route("/health")
def health():
    return {"status": "ok", "bot": "running"}

# -------------------------------------------------
# Bot & Scheduler (singletons)
# -------------------------------------------------
bot: Bot | None = None
scheduler: AsyncIOScheduler | None = None

async def async_publish_job():
    """Собираем, выбираем, публикуем."""
    logger.info("▶️ Starting publish job")
    if not config.BOT_TOKEN or not config.CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID missing")
        return

    items = await get_pinterest_images(config.PINTEREST_SEARCH_URL)
    if not items:
        logger.info("🔍 No pins found")
        return

    # выбираем непубликовавшийся
    random.shuffle(items)
    candidate = next((i for i in items if not is_published(i["id"])), None)
    if not candidate:
        logger.info("✅ All pins already published")
        return

    success = await publish_photo(bot, candidate["url"])
    if success:
        mark_as_published(candidate["id"])
        logger.info(f"✅ Pin {candidate['id']} published")
    else:
        logger.warning(f"❗ Pin {candidate['id']} NOT published – will retry later")

async def keep_alive():
    """Ping to self (Render needs a request every few minutes)."""
    url = "https://pinterest-to-teleg.onrender.com/health"
    try:
        async with ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                await resp.text()
        logger.debug("💓 keep_alive OK")
    except Exception as exc:
        logger.warning(f"💓 keep_alive failed: {exc}")

def start_bot_and_scheduler():
    """Инициализация — вызывается один раз при импорте (gunicorn) и в __main__."""
    global bot, scheduler
    if bot is not None:
        logger.warning("Bot already started – skipping")
        return

    logger.info("🚀 Initializing bot and scheduler")
    init_db()
    bot = Bot(token=config.BOT_TOKEN)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        async_publish_job,
        "interval",
        minutes=config.PUBLISH_DELAY_MINUTES,
        next_run_time=datetime.now() + timedelta(seconds=10),
        id="publish_job",
        misfire_grace_time=60,
    )
    scheduler.add_job(
        keep_alive,
        "interval",
        minutes=3,
        next_run_time=datetime.now() + timedelta(seconds=30),
        id="keepalive",
        misfire_grace_time=30,
    )
    scheduler.start()
    logger.info("✅ Scheduler started")

def _shutdown(*_):
    """Graceful stop – called on SIGINT / SIGTERM."""
    logger.info("🛑 Received termination signal – shutting down")
    if scheduler:
        scheduler.shutdown(wait=False)
    if bot:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.session.close())
    logger.info("✅ Shutdown complete")
    sys.exit(0)

# Register signal handlers (Render sends SIGTERM on restart)
signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

# -------------------------------------------------
# Run
# -------------------------------------------------
if __name__ == "__main__":
    # локальный запуск (no gunicorn)
    start_bot_and_scheduler()
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
else:
    # gunicorn импортирует `app` → сразу стартуем бота/шедулер
    start_bot_and_scheduler()
