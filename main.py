import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask

import config
from database import init_db, is_published, mark_as_published
from parser import get_pinterest_images
from publisher import publish_photo

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Flask app for Render Web Service (keeps the service alive)
app = Flask(__name__)

# Global bot instance
bot = None
scheduler = None

@app.route('/')
def home():
    return "Pinterest Bot is running! ✅"

@app.route('/health')
def health():
    return {"status": "ok", "bot": "running"}

async def job_publish_content():
    """
    Scheduled job that runs every 20 minutes (or as configured).
    It fetches content, picks ONE new item, and sends it.
    """
    logger.info("Starting scheduled job...")
    
    if not config.BOT_TOKEN or not config.CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID not set! check environment variables.")
        return

    # 1. Fetch content
    items = get_pinterest_images(config.PINTEREST_SEARCH_URL)
    
    if not items:
        logger.info("No items found.")
        return

    # 2. Find a candidate to publish
    candidate = None
    random.shuffle(items)
    
    for item in items:
        if not is_published(item['id']):
            candidate = item
            break
            
    if not candidate:
        logger.info("No new unpublished items found in this fetch.")
        return

    # 3. Publish
    logger.info(f"Attempting to publish: {candidate['id']}")
    success = await publish_photo(bot, candidate['url'])
    
    if success:
        mark_as_published(candidate['id'])
        logger.info(f"Published and marked as done: {candidate['id']}")
    else:
        logger.error("Failed to publish candidate.")

def init_bot():
    """Initialize bot and scheduler - called once when gunicorn worker starts"""
    global bot, scheduler
    
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set! Check environment variables.")
        return
        
    logger.info("Initializing Pinterest Bot...")
    init_db()
    
    bot = Bot(token=config.BOT_TOKEN)
    scheduler = AsyncIOScheduler()
    
    # Add job to run every 20 minutes
    scheduler.add_job(
        job_publish_content,
        'interval',
        minutes=config.PUBLISH_DELAY_MINUTES,
        next_run_time=datetime.now() + timedelta(seconds=10)
    )
    
    scheduler.start()
    logger.info(f"Pinterest Bot Started. Scheduler interval: {config.PUBLISH_DELAY_MINUTES} minutes.")

# Initialize bot when module is loaded (gunicorn worker start)
init_bot()

if __name__ == "__main__":
    # For local testing
    port = int(config.PORT) if hasattr(config, 'PORT') else 10000
    app.run(host='0.0.0.0', port=port, debug=False)
