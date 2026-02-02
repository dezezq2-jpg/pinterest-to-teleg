# Pinterest Telegram Bot

Автоматически публикует фото из Pinterest в Telegram канал каждые 20 минут.

## Deployment на Render

1. Загрузите код на GitHub
2. На Render создайте новый **Background Worker**
3. Подключите GitHub репозиторий
4. Добавьте переменные окружения:
   - `BOT_TOKEN` - ваш токен бота
   - `CHANNEL_ID` - ID канала (@bikinimood69)
   - `PINTEREST_SEARCH_URL` - URL поиска Pinterest

## Локальный запуск

```bash
pip install -r requirements.txt
python main.py
```
