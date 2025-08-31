#!/usr/bin/env python3
"""
Скрипт для локального тестування бота
Запуск: python test_local.py
"""

import os
import asyncio
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

# Тестові налаштування
os.environ['BOT_TOKEN'] = 'TEST_TOKEN'  # Замініть на справжній токен для тестування
os.environ['ADMIN_ID'] = '123456789'    # Замініть на ваш Telegram ID
# Для локального тестування не встановлюємо WEBHOOK_URL

def main():
    """Запуск бота в режимі polling для локального тестування"""
    print("🤖 Запуск бота в режимі тестування...")
    print("📝 Переконайтеся, що ви встановили правильний BOT_TOKEN")
    print("🔄 Бот працюватиме в polling режимі (без webhook)")
    print("⏹️ Для зупинки натисніть Ctrl+C")
    print("-" * 50)
    
    try:
        # Імпорт та запуск основного модуля
        from main import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n🛑 Бот зупинено користувачем")
    except Exception as e:
        print(f"❌ Помилка запуску: {e}")
        print("🔧 Перевірте налаштування та токен бота")

if __name__ == "__main__":
    main()