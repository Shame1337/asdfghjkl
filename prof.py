#!/usr/bin/env python3
"""
Telegram Profit Bot - Автоматически постит сообщения о профите в канал
Использует Bot API (обычный бот, не userbot)
"""
import asyncio
import random
import string
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# --- НАСТРОЙКИ БОТА ---
BOT_TOKEN = "8592252379:AAER20UAV9SkmmwatoktKvAGylAl5_LkPiI"
CHANNEL_USERNAME = "@deceptionprofits"  # Канал должен начинаться с @

MENTORS = [
    "ЗЕМНОЙ ДРОТИК",
]

# Диапазоны сумм (в рублях)
MIN_AMOUNT = 500
MAX_AMOUNT = 50000

# Интервалы времени между постами (в секундах)
MIN_INTERVAL = 3600    # 1 час
MAX_INTERVAL = 21600   # 6 часов


def generate_amount():
    """Генерирует случайную сумму с копейками для сумм до 15000₽"""
    amount = random.randint(MIN_AMOUNT, MAX_AMOUNT)
    
    if amount < 15000:
        # Добавляем копейки
        kopeks = random.randint(1, 99)
        return f"{amount:,}.{kopeks:02d}".replace(',', ' ')
    else:
        return f"{amount:,}".replace(',', ' ')


def generate_random_tag():
    """Генерирует случайный тег из букв и цифр (до 8 символов)"""
    length = random.randint(6, 8)
    chars = string.ascii_letters + string.digits
    tag = ''.join(random.choice(chars) for _ in range(length))
    return tag


def generate_worker():
    """Генерирует случайный тег или 'Аноним'"""
    choice = random.randint(1, 10)
    
    if choice <= 7:  # 70% - случайный тег
        return generate_random_tag()
    else:  # 30% - аноним
        return "Аноним"


def generate_mentor():
    """Генерирует наставника или 'Без наставника'"""
    if random.randint(1, 10) <= 7:  # 70% - есть наставник
        return random.choice(MENTORS)
    else:  # 30% - без наставника
        return "Без наставника"


def create_profit_message():
    """Создает сообщение о профите"""
    worker = generate_worker()
    amount = generate_amount()
    mentor = generate_mentor()
    
    message = f"""🌟 <b>НОВЫЙ ПРОФИТ!</b> 🌟

🧑‍💼 ВОРКЕР
┖ <b>#{worker}</b>

💰 СУММА
┖ <b>{amount} ₽</b>

🎯 НАСТАВНИК
┖ <b>{mentor}</b>

📂 НАПРАВЛЕНИЕ
┖  <b>NARKO ШАНТАЖ</b>

🎉 Поздравляем с профитом!"""
    
    return message


async def send_test_message(bot):
    """Отправляет тестовое сообщение для проверки"""
    try:
        message = create_profit_message()
        await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=message,
            parse_mode='HTML'
        )
        print("✅ Тестовое сообщение отправлено успешно!")
        return True
    except TelegramError as e:
        print(f"❌ Ошибка при отправке тестового сообщения: {e}")
        return False


async def main():
    """Основная функция бота"""
    print("🤖 Запуск Profit Bot (Bot API)...")
    print(f"📢 Канал: {CHANNEL_USERNAME}")
    print(f"⏰ Интервал: {MIN_INTERVAL//60}-{MAX_INTERVAL//60} минут")
    print("")
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Проверяем бота
        bot_info = await bot.get_me()
        print(f"✅ Бот запущен: @{bot_info.username}")
        print("")
        
        # Проверяем права в канале
        print("🔍 Проверяю доступ к каналу...")
        try:
            chat = await bot.get_chat(CHANNEL_USERNAME)
            print(f"✅ Канал найден: {chat.title}")
            
            # Проверяем права бота
            bot_member = await bot.get_chat_member(CHANNEL_USERNAME, bot_info.id)
            
            if bot_member.status not in ['administrator', 'creator']:
                print("")
                print("="*60)
                print("❌ БОТ НЕ ЯВЛЯЕТСЯ АДМИНИСТРАТОРОМ КАНАЛА!")
                print("="*60)
                print(f"Канал: {CHANNEL_USERNAME}")
                print("")
                print("📝 Что делать:")
                print(f"  1. Откройте канал {CHANNEL_USERNAME} в Telegram")
                print("  2. Нажмите: Настройки → Администраторы")
                print(f"  3. Добавьте бота @{bot_info.username}")
                print("  4. Дайте право 'Публиковать сообщения'")
                print("="*60)
                return
            
            if not bot_member.can_post_messages:
                print("")
                print("="*60)
                print("❌ У БОТА НЕТ ПРАВА ПУБЛИКОВАТЬ!")
                print("="*60)
                print(f"Бот: @{bot_info.username}")
                print("")
                print("📝 Включите право 'Публиковать сообщения' для бота")
                print("="*60)
                return
            
            print(f"✅ Бот имеет права администратора с публикацией")
            print("")
            
        except TelegramError as e:
            print(f"❌ Ошибка доступа к каналу: {e}")
            print("")
            print("Возможные причины:")
            print(f"  1. Канал {CHANNEL_USERNAME} не существует")
            print(f"  2. Бот не добавлен в канал")
            print(f"  3. Неверное имя канала (должно начинаться с @)")
            return
        
        # Отправляем тестовое сообщение
        print("📤 Отправляю тестовое сообщение...")
        if not await send_test_message(bot):
            print("")
            print("❌ Не удалось отправить тестовое сообщение")
            print("   Проверьте права бота в канале")
            return
        
        print("")
        print("🔄 Начинаю автоматическую публикацию...")
        print("   Нажмите Ctrl+C для остановки")
        print("")
        
        post_count = 1  # Тестовое сообщение уже отправлено
        
        while True:
            # Случайная задержка до следующего поста
            delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            delay_minutes = delay // 60
            delay_hours = delay // 3600
            
            if delay_hours > 0:
                print(f"💤 Следующий пост через ~{delay_hours} ч {(delay_minutes % 60)} мин...")
            else:
                print(f"💤 Следующий пост через {delay_minutes} минут...")
            
            await asyncio.sleep(delay)
            
            # Генерируем и отправляем сообщение
            message = create_profit_message()
            
            try:
                await bot.send_message(
                    chat_id=CHANNEL_USERNAME,
                    text=message,
                    parse_mode='HTML'
                )
                post_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now}] ✅ Пост #{post_count} отправлен!")
                print("")
                
            except TelegramError as e:
                print(f"❌ Ошибка при отправке: {e}")
                print("")
                
                if "forbidden" in str(e).lower() or "not enough rights" in str(e).lower():
                    print("❌ Бот потерял права в канале!")
                    print("   Проверьте права администратора")
                    break
    
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    finally:
        print("👋 Бот отключен")


if __name__ == "__main__":
    asyncio.run(main())
