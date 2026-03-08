import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

# Добавляем путь к корневой директории
sys.path.append(str(Path(__file__).parent.parent))

from aiogram.types import Update
from bot import dp, bot  # Импортируем из вашего основного файла

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_webhook(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """Обработчик webhook запросов от Telegram"""
    try:
        # Получаем данные запроса
        logger.info(f"Received update: {request_body.get('update_id')}")
        
        # Преобразуем в объект Update и передаем диспетчеру
        update = Update.model_validate(request_body, context={"bot": bot})
        await dp.feed_update(bot, update)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"ok": True})
        }
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# Vercel serverless функция
def webhook(request):
    """Точка входа для Vercel"""
    # Создаем новый event loop для каждого запроса
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Получаем тело запроса
        request_body = request.get_json()
        result = loop.run_until_complete(handle_webhook(request_body))
        return result
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
    finally:
        loop.close()