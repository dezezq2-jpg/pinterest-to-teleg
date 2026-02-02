from aiogram import Bot
from aiogram.types import BufferedInputFile
import logging
import asyncio
import config

logger = logging.getLogger(__name__)

async def publish_photo(bot: Bot, image_url: str):
    """
    Downloads the image and sends it to the channel.
    """
    try:
        # 1. Download image
        import requests
        response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        
        if response.status_code != 200:
            logger.error(f"Failed to download image {image_url}: {response.status_code}")
            return False
            
        file_bytes = response.content
        
        # 2. Send to Telegram
        # Using BufferedInputFile to send raw bytes
        photo_file = BufferedInputFile(file_bytes, filename="image.jpg")
        
        await bot.send_photo(
            chat_id=config.CHANNEL_ID,
            photo=photo_file,
            caption="" # User requested no captions
        )
        logger.info(f"Successfully sent image: {image_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending photo to Telegram: {e}")
        return False
