import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
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

# Flask app for Render Web Service
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

async def async_publish_job():
    """Async job to publish content"""
    logger.info("Starting scheduled job...")
    
    if not config.BOT_TOKEN or not config.CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID not set!")
        return

    # Fetch content
    items = get_pinterest_images(config.PINTEREST_SEARCH_URL)
    
    if not items:
        logger.info("No items found.")
        return

    # Find unpublished item
    candidate = None
    random.shuffle(items)
    
    for item in items:
        if not is_published(item['id']):
            candidate = item
            break
            
    if not candidate:
        logger.info("No new unpublished items found.")
        return

    # Publish
    logger.info(f"Attempting to publish: {candidate['id']}")
    success = await publish_photo(bot, candidate['url'])
    
    if success:
        mark_as_published(candidate['id'])
        logger.info(f"Published and marked as done: {candidate['id']}")
    else:
        logger.error("Failed to publish candidate.")

def job_wrapper():
    """Wrapper to run async job in sync scheduler"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_publish_job())
        loop.close()
    except Exception as e:
        logger.error(f"Error in job: {e}")

def init_bot():
    """Initialize bot and scheduler"""
    global bot, scheduler
    
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set!")
        return
        
    logger.info("Initializing Pinterest Bot...")
    init_db()
    
    bot = Bot(token=config.BOT_TOKEN)
    
    # Use BackgroundScheduler instead of AsyncIOScheduler
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        job_wrapper,
        'interval',
        minutes=config.PUBLISH_DELAY_MINUTES,
        next_run_time=datetime.now() + timedelta(seconds=10)
    )
    
    scheduler.start()
    logger.info(f"Pinterest Bot Started! Interval: {config.PUBLISH_DELAY_MINUTES} minutes.")

# Initialize when module loads
init_bot()

if __name__ == "__main__":
    port = int(config.PORT) if hasattr(config, 'PORT') else 10000
    app.run(host='0.0.0.0', port=port, debug=False)
