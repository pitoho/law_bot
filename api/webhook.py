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
        """Обрабатываем POST запросы от Telegram"""
        # Получаем длину тела запроса
        content_length = int(self.headers.get('Content-Length', 0))
        logger.debug(f"Received POST request, content length: {content_length}")
        
        # Читаем тело
        post_data = self.rfile.read(content_length)
        logger.debug(f"Raw post data: {post_data[:200]}...")  # Первые 200 символов
        
        # Парсим JSON
        try:
            update_data = json.loads(post_data.decode('utf-8'))
            logger.info(f"Successfully parsed JSON, update_id: {update_data.get('update_id')}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return
        
        # Проверяем наличие бота
        if not bot:
            logger.error("Bot instance is None!")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Bot not initialized')
            return
        
        # Асинхронно обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.debug("Creating Update object...")
            update = Update.model_validate(update_data, context={"bot": bot})
            
            logger.debug(f"Feeding update to dispatcher: {update.update_id}")
            loop.run_until_complete(dp.feed_update(bot, update))
            logger.info(f"Successfully processed update {update.update_id}")
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            logger.error(traceback.format_exc())
            
            # Отправляем ошибку
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "error": str(e),
                "traceback": traceback.format_exc().split('\n')
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
        finally:
            loop.close()
            logger.debug("Event loop closed")
    
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