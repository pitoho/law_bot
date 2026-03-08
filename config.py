import os
import logging

logger = logging.getLogger(__name__)

# Загружаем переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')

# Проверяем и конвертируем
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set in environment variables!")
    raise ValueError("BOT_TOKEN is required")

if not GROUP_ID:
    logger.error("GROUP_ID not set in environment variables!")
    raise ValueError("GROUP_ID is required")

try:
    GROUP_ID = int(GROUP_ID)
    logger.info(f"GROUP_ID converted to int: {GROUP_ID}")
except ValueError:
    logger.error(f"GROUP_ID must be an integer, got: {GROUP_ID}")
    raise

logger.info(f"Configuration loaded. BOT_TOKEN exists: {bool(BOT_TOKEN)}, GROUP_ID: {GROUP_ID}")