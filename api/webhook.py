import sys
import json
import asyncio
import logging
from pathlib import Path

# Добавляем корневую директорию в путь Python
sys.path.append(str(Path(__file__).parent.parent))

from bot import dp, bot
from aiogram.types import Update

logger = logging.getLogger(__name__)

# Переименовано с webhook на handler
async def async_handler(request_body):
    # ... (ваша асинхронная логика обработки) ...
    try:
        update = Update.model_validate(request_body, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"statusCode": 200, "body": json.dumps({"ok": True})}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# Главная синхронная функция, которую вызовет Vercel
def handler(request):
    """Точка входа для Vercel (должна называться handler)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Получаем JSON из запроса
        request_body = request.get_json()
        # Запускаем асинхронную обработку
        result = loop.run_until_complete(async_handler(request_body))
        return result
    except Exception as e:
        logger.error(f"Fatal: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal error"})}
    finally:
        loop.close()