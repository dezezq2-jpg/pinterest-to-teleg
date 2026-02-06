# publisher.py
import logging
from aiogram import Bot
from aiogram.types import URLInputFile
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
import config

logger = logging.getLogger(__name__)


async def _resolve_channel_id(bot: Bot) -> int:
    """
    Возвращает числовой chat_id.
    * Если CHANNEL_ID уже `int` – сразу возвращаем.
    * Если строка выглядит как число (в том числе с минусом) – конвертируем.
    * Иначе считаем, что передано имя/username и делаем get_chat().
    """
    # ✅ 1️⃣ Уже int – используем сразу
    if isinstance(config.CHANNEL_ID, int):
        return config.CHANNEL_ID

    # ✅ 2️⃣ Строка‑число → приводим к int
    raw = str(config.CHANNEL_ID).strip()
    if raw.lstrip("-").isdigit():
        return int(raw)

    # ✅ 3️⃣ Имя/username → запрашиваем у Telegram
    channel = raw.lstrip("@")
    chat = await bot.get_chat(channel)   # может бросить TelegramAPIError/BadRequest
    return chat.id


async def publish_photo(bot: Bot, image_url: str) -> bool:
    """
    Публикует изображение в канал.
    Возвращает True – если всё ОК, иначе False.
    """
    try:
        chat_id = await _resolve_channel_id(bot)

        await bot.send_photo(
            chat_id=chat_id,
            photo=URLInputFile(image_url),
            caption="",               # без подписи, как вы просили
        )
        logger.info(f"Successfully sent image: {image_url}")
        return True

    except TelegramForbiddenError:
        # Бот не в канале или нет прав
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
        # Любой другой API‑ошибочный код (400, 429, 500 и т.п.)
        logger.error(f"Telegram API error while sending: {exc}")
        return False

    except Exception as exc:
        # Неожиданные исключения – логируем трейc
        logger.exception(f"Unexpected error in publish_photo: {exc}")
        return False
