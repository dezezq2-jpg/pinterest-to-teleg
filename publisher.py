from aiogram import Bot
from aiogram.types import BufferedInputFile, URLInputFile
import logging
import config

logger = logging.getLogger(__name__)

async def publish_photo(bot: Bot, image_url: str):
    """
    Sends image to the channel using URL directly.
    """
    try:
        # Use URLInputFile - aiogram will download it asynchronously
        photo = URLInputFile(image_url)
        
        await bot.send_photo(
            chat_id=config.CHANNEL_ID,
            photo=photo,
            caption=""  # No captions as requested
        )
        
        logger.info(f"Successfully sent image: {image_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending photo to Telegram: {e}")
        return False
