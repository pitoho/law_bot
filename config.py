import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
SUPPORT_TOPIC_ID = int(os.getenv("SUPPORT_TOPIC_ID"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")