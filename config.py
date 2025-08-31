import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
AI_API_KEY = os.getenv('AI_API_KEY', 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjBmMjc2NjJhLWVhMGUtNGRlZC05MDQ1LTcyNzJiNWI4ZjZlNyIsImV4cCI6NDkxMDI1MzU5Mn0.P1IFARUejNIkl9RbQ7Ynpp-CZZegzYo3ed7ynRGCBrgvWp6ZcaaSoIKUUMjBADlojgLmOQZXC6uMxagqrIsjew')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Настройки подписок
DAILY_FREE_MESSAGES = 20
SUBSCRIPTION_PLANS = {
    '1month': {'name': '1 месяц', 'price': '200₴', 'duration_days': 30},
    '6months': {'name': '6 месяцев', 'price': '1000₴', 'duration_days': 180},
    '12months': {'name': '12 месяцев', 'price': '1800₴', 'duration_days': 365},
    'lifetime': {'name': 'Навсегда', 'price': '3999₴', 'duration_days': -1}
}

# Настройки AI API
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
# Попробуем использовать рабочую модель из списка
AI_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

# Настройки для Railway деплоя
PORT = int(os.getenv('PORT', 5000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

print("✅ Конфигурация загружена успешно!")
print(f"🤖 Порт для деплоя: {PORT}")
print(f"🔗 Webhook URL: {WEBHOOK_URL}")