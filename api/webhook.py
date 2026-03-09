import sys
import os
import json
import asyncio
import logging
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Добавляем корневую директорию в путь Python
sys.path.append(str(Path(__file__).parent.parent))

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем модули бота
try:
    from bot import dp, bot
    from config import BOT_TOKEN, GROUP_ID
    from aiogram.types import Update
    logger.info(f"Successfully imported bot modules. GROUP_ID: {GROUP_ID}, BOT_TOKEN exists: {bool(BOT_TOKEN)}")
except Exception as e:
    logger.error(f"Failed to import bot modules: {e}")
    logger.error(traceback.format_exc())
    raise

class handler(BaseHTTPRequestHandler):
    """Класс-обработчик для Vercel"""
    
    def log_message(self, format, *args):
        """Переопределяем логирование для совместимости с нашим логгером"""
        logger.info(f"{self.address_string()} - {format % args}")
    
def do_POST(self):
    """Минимальная версия обработчика"""
    content_length = int(self.headers.get('Content-Length', 0))
    post_data = self.rfile.read(content_length)
    
    try:
        update_data = json.loads(post_data.decode('utf-8'))
    except Exception as e:
        self.send_response(400)
        self.end_headers()
        return
    
    # Используем новый event loop для каждого запроса
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Создаём Update и обрабатываем
        update = Update.model_validate(update_data, context={"bot": bot})
        
        # Запускаем обработку синхронно
        loop.run_until_complete(dp.feed_update(bot, update))
        
        # Отправляем ответ
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Error: {e}")
        self.send_response(500)
        self.end_headers()
        self.wfile.write(str(e).encode('utf-8'))
        
    finally:
        # Закрываем loop
        loop.close()
    
    def do_GET(self):
        """Обработка GET запросов (для тестирования)"""
        logger.info("Received GET request")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
            <html>
                <body>
                    <h1>Telegram Bot Webhook</h1>
                    <p>This endpoint accepts POST requests from Telegram.</p>
                    <p>Status: Running</p>
                </body>
            </html>
        """)