# publisher.py
import logging
from aiogram import Bot
from aiogram.types import URLInputFile
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError

import config

logger = logging.getLogger(__name__)


async def _resolve_channel_id(bot: Bot) -> int:
    """Если в config.CHANNEL_ID указано @username, получаем реальный ID."""
    if isinstance(config.CHANNEL_ID, int):
        return config.CHANNEL_ID
    channel = config.CHANNEL_ID.lstrip("@")
    try:
        chat = await bot.get_chat(channel)
        return chat.id
    except Exception as exc:
        logger.error(f"Unable to resolve channel ID for {channel}: {exc}")
        raise


async def publish_photo(bot: Bot, image_url: str) -> bool:
    """
    Отправка фото в канал.
    Возвращает True/False.
    """
    try:
        chat_id = await _resolve_channel_id(bot)
        await bot.send_photo(
            chat_id=chat_id,
            photo=URLInputFile(image_url),
            caption="",  # без подписи
        )
        logger.info(f"Successfully sent image: {image_url}")
        return True

    except TelegramForbiddenError:
        msg = (
            f"❌ Ошибка: бот не является членом канала {config.CHANNEL_ID}. "
            "Проверьте, что он добавлен и имеет права администратора."
        )
        logger.error(msg)
        if config.ADMIN_ID:
            try:
                await bot.send_message(config.ADMIN_ID, msg)
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")
        return False

    except TelegramAPIError as exc:
        logger.error(f"Telegram API error while sending: {exc}")
        return False

    except Exception as exc:
        logger.exception(f"Unexpected error in publish_photo: {exc}")
        return False
