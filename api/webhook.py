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
        """Обрабатываем POST запросы от Telegram"""
        # Получаем длину тела запроса
        content_length = int(self.headers.get('Content-Length', 0))
        logger.debug(f"Received POST request, content length: {content_length}")
        
        # Читаем тело
        post_data = self.rfile.read(content_length)
        logger.debug(f"Raw post data: {post_data[:200]}...")
        
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
        
        # ГАРАНТИРОВАННО СОЗДАЁМ НОВЫЙ EVENT LOOP
        loop = None
        response_sent = False
        
        try:
            # Создаём новый event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.debug("Created new event loop")
            
            # Создаём Update объект
            update = Update.model_validate(update_data, context={"bot": bot})
            logger.debug(f"Created Update object for update {update.update_id}")
            
            # Функция для обработки обновления
            async def process_update():
                try:
                    logger.debug(f"Starting to feed update {update.update_id}")
                    await dp.feed_update(bot, update)
                    logger.debug(f"Successfully fed update {update.update_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error in feed_update: {e}")
                    logger.error(traceback.format_exc())
                    raise
            
            # Запускаем обработку и ждём результата
            logger.debug("Running process_update in event loop")
            result = loop.run_until_complete(process_update())
            
            if result:
                logger.info(f"Successfully processed update {update.update_id}")
                # Отправляем успешный ответ
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
                response_sent = True
            
        except asyncio.CancelledError:
            logger.error("Task was cancelled")
            if not response_sent:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Task cancelled')
                
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            logger.error(traceback.format_exc())
            
            if not response_sent:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {
                    "error": str(e),
                    "traceback": traceback.format_exc().split('\n')
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        finally:
            # ОЧЕНЬ ВАЖНО: Правильно закрываем loop
            if loop:
                logger.debug("Cleaning up event loop")
                
                # Отменяем все запущенные задачи
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.debug(f"Cancelling {len(pending)} pending tasks")
                    for task in pending:
                        task.cancel()
                    
                    # Даём время задачам на отмену
                    if not loop.is_closed():
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Останавливаем loop
                if loop.is_running():
                    logger.debug("Stopping running loop")
                    loop.stop()
                
                # Закрываем loop
                if not loop.is_closed():
                    logger.debug("Closing event loop")
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