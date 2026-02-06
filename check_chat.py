import asyncio
from aiogram import Bot
import config

async def main():
    bot = Bot(token=config.BOT_TOKEN)

    # Попытка использовать уже‑записанный ID
    try:
        chat = await bot.get_chat(config.CHANNEL_ID)   # если это число – будет работать
        print("✅ Chat found by numeric ID")
    except Exception:
        # Если в переменной вместо id записано имя – пробуем по имени
        chat = await bot.get_chat("@bikinimood69")
        print("✅ Chat found by @username")

    print(f"ID      : {chat.id}")
    print(f"Title   : {chat.title}")
    print(f"Type    : {chat.type}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
