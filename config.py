import os
from dotenv import load_dotenv

load_dotenv()

# Налаштування бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Налаштування веб-сервера
WEBHOOK_PATH = "/webhook"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", "8000"))

# Перевірка наявності токена
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не знайдено в змінних середовища")