import sys
import json
import asyncio
import logging
import traceback
from pathlib import Path
from http.server import BaseHTTPRequestHandler

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from bot import dp, bot
from aiogram.types import Update

# Один loop на весь инстанс Vercel function
LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(LOOP)


async def process_update(update_data: dict):
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            update_data = json.loads(post_data.decode("utf-8"))

            LOOP.run_until_complete(process_update(update_data))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        except Exception as e:
            logger.error("Error in feed_update: %s", e)
            logger.error(traceback.format_exc())

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
            )

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Webhook is running")