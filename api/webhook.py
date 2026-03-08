# api/webhook.py
import sys
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from bot import dp, bot
from aiogram.types import Update

class handler(BaseHTTPRequestHandler):
    """Класс-обработчик для Vercel"""
    
    def do_POST(self):
        """Обрабатываем POST запросы от Telegram"""
        # Получаем длину тела запроса
        content_length = int(self.headers.get('Content-Length', 0))
        # Читаем тело
        post_data = self.rfile.read(content_length)
        
        # Парсим JSON
        try:
            update_data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return
        
        # Асинхронно обрабатываем обновление
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            update = Update.model_validate(update_data, context={"bot": bot})
            loop.run_until_complete(dp.feed_update(bot, update))
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        except Exception as e:
            # Отправляем ошибку
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            loop.close()
    
    # Vercel может вызвать и GET, поэтому добавим заглушку
    def do_GET(self):
        self.send_response(405)  # Method Not Allowed
        self.end_headers()
        self.wfile.write(b'Method not allowed. Use POST for webhook.')