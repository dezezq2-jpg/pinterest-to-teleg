import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

# Initialize Bot
bot = Bot(token=config.BOT_TOKEN) if config.BOT_TOKEN else None

async def job_publish_content():
    """
    Scheduled job that runs every 20 minutes (or as configured).
    It fetches content, picks ONE new item, and sends it.
    """
    logger.info("Starting scheduled job...")
    
    if not config.BOT_TOKEN or not config.CHANNEL_ID:
        logger.error("BOT_TOKEN or CHANNEL_ID not set! check .env file.")
        return

    # 1. Fetch content
    items = get_pinterest_images(config.PINTEREST_SEARCH_URL)
    
    if not items:
        logger.info("No items found.")
        return

    # 2. Find a candidate to publish
    # We only want to publish 1 item per cycle (every 20 mins)
    candidate = None
    
    # Shuffle to get random variety if multiple are new
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

async def main():
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set! Please edit .env or config.py")
        # return # User might want to run it anyway to test scraper? No, bot will fail.
        
    init_db()
    
    # Send a startup message or log
    logger.info("Pinterest Bot Started.")
    
    scheduler = AsyncIOScheduler()
    
    # Add job to run every 20 minutes
    # We also run it immediately (after a short delay) to start
    scheduler.add_job(
        job_publish_content,
        'interval',
        minutes=config.PUBLISH_DELAY_MINUTES,
        next_run_time=datetime.now() + timedelta(seconds=5)
    )
    
    scheduler.start()
    logger.info(f"Scheduler started. Interval: {config.PUBLISH_DELAY_MINUTES} minutes.")
    
    # Keep alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
