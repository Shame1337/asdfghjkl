#!/usr/bin/env python3
"""
DECEPTION TEAM Moderation Bot
Бот для модерации группы с командами администрирования и статистикой
Улучшенная версия с расширенной функциональностью
"""
import asyncio
import re
import json
import os
import random
import html
import requests
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8333850560:AAFAP3TGp_2GAraqksxX2KilcTbQCjIIBCE"
ADMIN_IDS = [8495992108, 8238414921]

# Файл для хранения данных
DATA_FILE = "bot_data.json"
# Значения по умолчанию для карты (если еще не заданы в файле)
DEFAULT_CARD_NUMBER = "4400 0000 0000 0000"
DEFAULT_CARD_BANK = "Банк не задан"

# API настройки для генерации изображений
API_URL = "https://api.airforce/v1/images/generations"
API_KEY = "sk-air-xI5dcD8u4JyCnsmA4NuY21rYrV9pPlmrNwMiywh67MbTwaj8TczYHDyR9p2Inmll"
PROFIT_GROUP_ID = -1003608461364

# Список сообщений для периодической рассылки
WORKER_MESSAGES = [
    """👋 <b>Дорогие воркеры</b> наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт ваших сообщений вступить в ученики 

💼 Приятного ворка в нашей тиме""",
    
    """👋 <b>Дорогие воркеры!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) открывает набор в ученики 

📩 Ждём ваших сообщений для вступления в команду 

💼 Удачи в работе!""",
    
    """⚠️ <b>Воркеры, внимание!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) набирает учеников 

✍️ Пишите для вступления в нашу команду 

💼 Приятного ворка!""",
    
    """👋 <b>Дорогие воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт вас в ученики 

📩 Отправляйте сообщения для вступления 

💼 Хорошего ворка в нашей тиме!""",
    
    """👋 <b>Воркеры!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) открыт для новых учеников 

📩 Ждём ваших сообщений 

💼 Приятного ворка в команде!""",
    
    """👋 <b>Дорогие воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) приглашает в ученики 

✍️ Пишите для вступления в нашу тиму 

💼 Удачи в ворке!""",
    
    """⚠️ <b>Воркеры, внимание!</b> <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) набирает учеников 

📩 Ждём ваших сообщений для вступления 

💼 Приятного ворка в нашей команде!""",
    
    """👋 <b>Дорогие воркеры!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт новых учеников 

📩 Отправляйте сообщения для вступления в тиму 

💼 Хорошего ворка!""",
    
    """👋 <b>Воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) открывает набор в ученики 

✍️ Пишите для вступления в команду 

💼 Приятного ворка в нашей тиме!""",
    
    """👋 <b>Дорогие воркеры!</b> <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) приглашает в ученики 

📩 Ждём ваших сообщений 

💼 Удачи в ворке в нашей команде!""",
    
    """⚠️ <b>Воркеры, внимание!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) набирает учеников 

📩 Отправляйте сообщения для вступления 

💼 Приятного ворка в тиме!""",
    
    """👋 <b>Дорогие воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт вас в ученики 

✍️ Пишите для вступления в нашу команду 

💼 Хорошего ворка!""",
    
    """👋 <b>Воркеры!</b> <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) открыт для новых учеников 

📩 Ждём ваших сообщений для вступления в тиму 

💼 Приятного ворка в команде!""",
    
    """👋 <b>Дорогие воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) приглашает в ученики 

📩 Отправляйте сообщения для вступления 

💼 Удачи в ворке в нашей тиме!""",
    
    """⚠️ <b>Воркеры, внимание!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) набирает учеников 

✍️ Пишите для вступления в команду 

💼 Приятного ворка!""",
    
    """👋 <b>Дорогие воркеры!</b> <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт новых учеников 

📩 Ждём ваших сообщений 

💼 Хорошего ворка в нашей тиме!""",
    
    """👋 <b>Воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) открывает набор в ученики 

📩 Отправляйте сообщения для вступления в тиму 

💼 Приятного ворка в команде!""",
    
    """👋 <b>Дорогие воркеры!</b> Наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) приглашает в ученики 

✍️ Пишите для вступления в нашу команду 

💼 Удачи в ворке!""",
    
    """⚠️ <b>Воркеры, внимание!</b> <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) набирает учеников 

📩 Ждём ваших сообщений для вступления 

💼 Приятного ворка в нашей тиме!""",
    
    """👋 <b>Дорогие воркеры</b>, наставник <b>"ЗЕМНОЙ ДРОТИК"</b> ( нарко шантаж ) ждёт вас в ученики 

📩 Отправляйте сообщения для вступления 

💼 Хорошего ворка в команде!"""
]

# --- ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ ---
def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Гарантируем наличие ключей для карты
                if "card_number" not in data:
                    data["card_number"] = DEFAULT_CARD_NUMBER
                if "card_bank" not in data:
                    data["card_bank"] = DEFAULT_CARD_BANK
                return data
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    return {
        "warns": {},
        "workers": {},
        "users": {},
        "command_cooldowns": {},
        "last_bot_messages": {},
        "spam_counts": {},
        "link_violations": {},  # Отслеживание нарушений по ссылкам
        "card_number": DEFAULT_CARD_NUMBER,
        "card_bank": DEFAULT_CARD_BANK,
    }

def save_data():
    """Сохранение данных в файл"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(bot_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")

# Глобальные данные
bot_data = load_data()

def update_user_info(user):
    """Обновляет информацию о пользователе"""
    user_id = str(user.id)
    if "users" not in bot_data:
        bot_data["users"] = {}
    
    bot_data["users"][user_id] = {
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "last_seen": datetime.now().isoformat()
    }
    save_data()

# --- АНТИСПАМ ДЛЯ КОМАНД ---
async def check_command_spam(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str, cooldown_seconds: int = 5) -> bool:
    """
    Проверяет можно ли использовать команду (антиспам)
    Возвращает True если можно использовать, False если нужно подождать
    """
    user_id = str(update.effective_user.id)
    current_time = datetime.now().timestamp()
    
    # Инициализация структур
    if "command_cooldowns" not in bot_data:
        bot_data["command_cooldowns"] = {}
    if user_id not in bot_data["command_cooldowns"]:
        bot_data["command_cooldowns"][user_id] = {}
        
    if "spam_counts" not in bot_data:
        bot_data["spam_counts"] = {}
    if user_id not in bot_data["spam_counts"]:
        bot_data["spam_counts"][user_id] = {
            "count": 0,
            "last_spam": 0
        }
    
    # Проверяем последнее использование команды
    if command_name in bot_data["command_cooldowns"][user_id]:
        last_use = bot_data["command_cooldowns"][user_id][command_name]
        time_passed = current_time - last_use
        
        if time_passed < cooldown_seconds:
            # Увеличиваем счетчик спама
            bot_data["spam_counts"][user_id]["count"] += 1
            bot_data["spam_counts"][user_id]["last_spam"] = current_time
            save_data()
            
            # Если спам счетчик >= 3, выдаем варн
            if bot_data["spam_counts"][user_id]["count"] >= 3:
                bot_data["spam_counts"][user_id]["count"] = 0
                
                # Выдаем варн
                if "warns" not in bot_data:
                    bot_data["warns"] = {}
                if user_id not in bot_data["warns"]:
                    bot_data["warns"][user_id] = []
                
                bot_data["warns"][user_id].append({
                    "reason": "Спам командами",
                    "date": datetime.now().isoformat(),
                    "admin": "Система"
                })
                save_data()
                
                warn_count = len(bot_data["warns"][user_id])
                
                message_text = (
                    f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
                    f"👤 Пользователь: {update.effective_user.mention_html()}\n"
                    f"📝 Причина: <b>Спам командами</b>\n"
                    f"🔢 Предупреждений: <b>{warn_count}/3</b>\n\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await send_auto_delete_message(context, update.effective_chat.id, message_text)
                
                # Проверка на бан
                if warn_count >= 3:
                    try:
                        await context.bot.ban_chat_member(update.effective_chat.id, int(user_id))
                        ban_text = (
                            f"🔨 <b>БАН ЗА 3 ПРЕДУПРЕЖДЕНИЯ</b>\n\n"
                            f"👤 Пользователь: {update.effective_user.mention_html()}\n"
                            f"📝 Причина: Накоплено 3 предупреждения"
                        )
                        await send_auto_delete_message(context, update.effective_chat.id, ban_text)
                    except Exception as e:
                        print(f"Ошибка бана: {e}")
            
            # Молча удаляем команду
            try:
                await update.message.delete()
            except:
                pass
            return False
            
    # Сбрасываем счетчик спама если прошло достаточно времени (30 сек)
    if current_time - bot_data["spam_counts"][user_id]["last_spam"] > 30:
        bot_data["spam_counts"][user_id]["count"] = 0

    # Перед выполнением новой команды удаляем старое сообщение бота пользователю
    if "last_bot_messages" in bot_data and user_id in bot_data["last_bot_messages"]:
        last_msg = bot_data["last_bot_messages"][user_id]
        try:
            await context.bot.delete_message(chat_id=last_msg['chat_id'], message_id=last_msg['message_id'])
        except:
            pass
        del bot_data["last_bot_messages"][user_id]
        save_data()

    # Обновляем время последнего использования
    bot_data["command_cooldowns"][user_id][command_name] = current_time
    save_data()
    return True

# --- АВТОУДАЛЕНИЕ СООБЩЕНИЙ ---
async def send_auto_delete_message(context, chat_id, text, parse_mode='HTML', countdown=10):
    """Отправляет сообщение с обратным отсчетом и автоудалением"""
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"{text}\n\n⏱ <i>Удаление через: {countdown} сек</i>",
            parse_mode=parse_mode
        )
        
        async def delete_process():
            for i in range(countdown - 1, 0, -1):
                await asyncio.sleep(1)
                try:
                    await message.edit_text(
                        f"{text}\n\n⏱ <i>Удаление через: {i} сек</i>",
                        parse_mode=parse_mode
                    )
                except:
                    pass
            
            await asyncio.sleep(1)
            try:
                await message.delete()
            except:
                pass

        asyncio.create_task(delete_process())
        return message
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return None

# --- ПРОВЕРКА ПРАВ ---
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверка по списку ADMIN_IDS
    if ADMIN_IDS and user_id in ADMIN_IDS:
        print(f"✅ Пользователь {user_id} найден в ADMIN_IDS")
        return True
    
    # Проверка по статусу в чате
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_chat_admin = member.status in ['creator', 'administrator']
        print(f"{'✅' if is_chat_admin else '❌'} Статус пользователя {user_id} в чате: {member.status}")
        return is_chat_admin
    except Exception as e:
        print(f"⚠️ Ошибка проверки прав для пользователя {user_id}: {e}")
        return False

# --- ПАРСИНГ ВРЕМЕНИ ---
def parse_time(time_str: str) -> int:
    """Парсит строку времени в секунды"""
    if not time_str:
        return 0
    
    time_str = time_str.lower().strip()
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    
    try:
        if time_str == "permanent" or time_str == "perm":
            return 0
        if time_str[-1] in multipliers:
            return int(time_str[:-1]) * multipliers[time_str[-1]]
        return int(time_str)
    except:
        return 0

def format_time(seconds: int) -> str:
    """Форматирует секунды в читаемый формат"""
    if seconds == 0:
        return "навсегда"
    
    weeks = seconds // 604800
    days = (seconds % 604800) // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if weeks > 0:
        parts.append(f"{weeks}н")
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    
    return " ".join(parts) if parts else f"{seconds}с"

# --- КОМАНДЫ МОДЕРАЦИИ ---
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mute - замутить пользователя"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для мута!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    
    # Проверка на попытку замутить бота
    bot_info = await context.bot.get_me()
    if user.id == bot_info.id:
        return
    
    time_str = context.args[0] if context.args else "1h"
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Нарушение правил"
    
    duration = parse_time(time_str)
    until_date = datetime.now() + timedelta(seconds=duration) if duration > 0 else None
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        time_display = format_time(duration) if duration > 0 else "навсегда"
        
        message_text = (
            f"🔇 <b>МЬЮТ ВЫДАН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"⏱ Время: <b>{time_display}</b>\n"
            f"📝 Причина: {reason}\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось замутить пользователя:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ban - забанить пользователя"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для бана!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    
    # Проверка на попытку забанить бота
    bot_info = await context.bot.get_me()
    if user.id == bot_info.id:
        return
    
    time_str = context.args[0] if context.args else "permanent"
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Нарушение правил"
    
    duration = parse_time(time_str)
    until_date = datetime.now() + timedelta(seconds=duration) if duration > 0 else None
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            until_date=until_date
        )
        
        time_display = format_time(duration) if duration > 0 else "навсегда"
        
        message_text = (
            f"🔨 <b>БАН ВЫДАН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"⏱ Время: <b>{time_display}</b>\n"
            f"📝 Причина: {reason}\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось забанить пользователя:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /kick - кикнуть пользователя"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для кика!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    reason = " ".join(context.args) if context.args else "Нарушение правил"
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        
        message_text = (
            f"👢 <b>КИК ВЫПОЛНЕН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"📝 Причина: {reason}\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось кикнуть пользователя:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def kicku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /kicku - массовый кик пользователей"""
    if not await is_admin(update, context):
        return

    if not context.args:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "⚠️ <b>ИСПОЛЬЗОВАНИЕ</b>\n\n"
            "Укажите юзернеймы через пробел:\n"
            "<code>/kicku @user1 @user2 @user3</code>",
            countdown=5
        )
        return

    ids_to_kick = set()
    targets = {}
    admin = update.effective_user
    
    # Собираем ID из entities
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'text_mention' and entity.user:
                ids_to_kick.add(entity.user.id)
                targets[f"@{entity.user.username or entity.user.first_name}"] = {
                    "id": entity.user.id, "resolved": True
                }

    # Создаем карту username -> user_id из БД
    username_to_id = {}
    if "users" in bot_data:
        for uid, info in bot_data["users"].items():
            if info.get("username"):
                username_to_id[info["username"].lower()] = uid

    # Проходимся по аргументам
    for arg in context.args:
        clean_arg = arg.lstrip('@').strip(',')
        lower_arg = clean_arg.lower()
        
        user_id = None
        
        # Пробуем ID
        if clean_arg.isdigit():
            user_id = int(clean_arg)
        
        # Пробуем БД
        if not user_id:
            user_id = username_to_id.get(lower_arg)
        
        # Пробуем API
        error_reason = None
        if not user_id:
            try:
                await asyncio.sleep(0.2)
                search_query = f"@{clean_arg}"
                chat_obj = await context.bot.get_chat(search_query)
                user_id = chat_obj.id
            except Exception as e:
                error_reason = str(e)

        if user_id:
            ids_to_kick.add(user_id)
            targets[arg] = {"id": user_id, "resolved": True}
        else:
            if arg not in targets:
                targets[arg] = {"resolved": False, "error": error_reason or "Не удалось определить ID"}

    # Выполняем кик
    kicked_users = []
    errors = []

    for uid in ids_to_kick:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, uid)
            await context.bot.unban_chat_member(update.effective_chat.id, uid)
            
            name = str(uid)
            for k, v in targets.items():
                if v.get("id") == uid:
                    name = k
                    break
            kicked_users.append(name)
        except Exception as e:
            errors.append(f"ID {uid}: {str(e)}")

    # Добавляем ошибки разрешения имен
    for name, info in targets.items():
        if not info.get("resolved"):
            errors.append(f"{name}: {info.get('error')}")

    # Формируем отчет
    message_text = (
        f"👢 <b>МАССОВЫЙ КИК</b>\n\n"
        f"👮 Администратор: {admin.mention_html()}\n\n"
    )
    
    if kicked_users:
        message_text += f"✅ <b>Кикнуты ({len(kicked_users)}):</b>\n"
        for user in kicked_users[:10]:  # Ограничиваем вывод
            message_text += f"• {user}\n"
        if len(kicked_users) > 10:
            message_text += f"... и еще {len(kicked_users) - 10}\n"
        message_text += "\n"
        
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n... и еще {len(errors) - 5} ошибок"
        message_text += f"❌ <b>Ошибки ({len(errors)}):</b>\n{error_msg}"

    await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=15)

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /warn - выдать предупреждение"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для выдачи предупреждения!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    reason = " ".join(context.args) if context.args else "Нарушение правил"
    
    user_id = str(user.id)
    if "warns" not in bot_data:
        bot_data["warns"] = {}
    if user_id not in bot_data["warns"]:
        bot_data["warns"][user_id] = []
    
    bot_data["warns"][user_id].append({
        "reason": reason,
        "date": datetime.now().isoformat(),
        "admin": admin.username or admin.first_name
    })
    save_data()
    
    warn_count = len(bot_data["warns"][user_id])
    
    message_text = (
        f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ ВЫДАНО</b>\n\n"
        f"👤 Пользователь: {user.mention_html()}\n"
        f"👮 Администратор: {admin.mention_html()}\n"
        f"📝 Причина: {reason}\n"
        f"🔢 Предупреждений: <b>{warn_count}/3</b>\n\n"
        f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    if warn_count >= 3:
        message_text += "\n\n🔨 <b>Достигнут лимит предупреждений!</b>"
    
    await send_auto_delete_message(context, update.effective_chat.id, message_text)
    
    if warn_count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            ban_text = (
                f"🔨 <b>АВТОБАН ЗА 3 ПРЕДУПРЕЖДЕНИЯ</b>\n\n"
                f"👤 Пользователь: {user.mention_html()}\n"
                f"📝 Причина: Накоплено 3 предупреждения"
            )
            await send_auto_delete_message(context, update.effective_chat.id, ban_text)
        except Exception as e:
            print(f"Ошибка автобана: {e}")

# --- КОМАНДЫ ОТМЕНЫ ---
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unmute - снять мут"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для снятия мута!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
        
        message_text = (
            f"🔊 <b>РАЗМУТ ВЫПОЛНЕН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"✅ Мут успешно снят\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось снять мут:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unban - разбанить"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для разбана!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    
    try:
        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            only_if_banned=True
        )
        
        message_text = (
            f"✅ <b>РАЗБАН ВЫПОЛНЕН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"✅ Бан успешно снят\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось разбанить:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def unwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unwarn - снять предупреждение"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        await send_auto_delete_message(
            context, update.effective_chat.id,
            "❌ <b>ОШИБКА</b>\n\nОтветьте на сообщение пользователя для снятия предупреждения!",
            countdown=5
        )
        return
    
    user = update.message.reply_to_message.from_user
    admin = update.effective_user
    user_id = str(user.id)
    
    if "warns" not in bot_data:
        bot_data["warns"] = {}
    
    if user_id in bot_data["warns"] and bot_data["warns"][user_id]:
        bot_data["warns"][user_id].pop()
        save_data()
        
        warn_count = len(bot_data["warns"][user_id])
        
        message_text = (
            f"✅ <b>ПРЕДУПРЕЖДЕНИЕ СНЯТО</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"👮 Администратор: {admin.mention_html()}\n"
            f"🔢 Предупреждений осталось: <b>{warn_count}/3</b>\n\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    else:
        message_text = (
            f"ℹ️ <b>ИНФОРМАЦИЯ</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"✅ У пользователя нет предупреждений"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=5)

# --- УЛУЧШЕННАЯ ЗАЩИТА ОТ ССЫЛОК ---
def detect_links(text: str) -> list:
    """Обнаруживает все типы ссылок в тексте (исключая упоминания юзернеймов)"""
    patterns = [
        r'https?://[^\s]+',  # HTTP/HTTPS ссылки
        r'www\.[^\s]+',  # WWW ссылки
        r't\.me/[^\s]+',  # Telegram ссылки
        r'telegram\.me/[^\s]+',  # Telegram.me ссылки
        r'bit\.ly/[^\s]+',  # Короткие ссылки
        r'tinyurl\.com/[^\s]+',  # Короткие ссылки
        r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',  # Общий паттерн доменов
    ]
    
    found_links = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_links.extend(matches)
    
    # Фильтруем ложные срабатывания (обычные слова)
    filtered = []
    false_positives = ['www', 'com', 'net', 'org', 'ru', 'io']
    
    for link in found_links:
        # Проверяем что это не просто слово
        if any(link.lower().startswith(fp) and len(link) < 5 for fp in false_positives):
            continue
        # Проверяем что есть хотя бы точка или слэш (но НЕ упоминания @username)
        if ('.' in link or '/' in link or 't.me' in link.lower()) and not link.startswith('@'):
            filtered.append(link)
    
    return list(set(filtered))  # Убираем дубликаты

async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Улучшенная проверка сообщений на спам и ссылки"""
    message = update.message
    
    if not message:
        return
    
    # Пропускаем сообщения от бота
    if message.from_user and message.from_user.is_bot:
        return
    
    # Пропускаем админов
    if await is_admin(update, context):
        return
    
    # Проверяем только текстовые сообщения
    text = None
    if message.text:
        text = message.text
    elif message.caption:
        text = message.caption
    
    if not text:
        return
    
    # Обнаруживаем ссылки
    links = detect_links(text)
    
    if links:
        try:
            await message.delete()
            
            user_id = str(message.from_user.id)
            
            # Инициализация структур
            if "warns" not in bot_data:
                bot_data["warns"] = {}
            if user_id not in bot_data["warns"]:
                bot_data["warns"][user_id] = []
            
            if "link_violations" not in bot_data:
                bot_data["link_violations"] = {}
            if user_id not in bot_data["link_violations"]:
                bot_data["link_violations"][user_id] = {
                    "count": 0,
                    "last_violation": datetime.now().isoformat()
                }
            
            # Увеличиваем счетчик нарушений
            bot_data["link_violations"][user_id]["count"] += 1
            bot_data["link_violations"][user_id]["last_violation"] = datetime.now().isoformat()
            
            # Выдаем предупреждение
            bot_data["warns"][user_id].append({
                "reason": f"Отправка ссылок ({len(links)} шт.)",
                "date": datetime.now().isoformat(),
                "admin": "Система"
            })
            save_data()
            
            warn_count = len(bot_data["warns"][user_id])
            violation_count = bot_data["link_violations"][user_id]["count"]
            
            warning_msg_text = (
                f"🚫 <b>ЗАПРЕЩЕНО ОТПРАВЛЯТЬ ССЫЛКИ!</b>\n\n"
                f"👤 Пользователь: {message.from_user.mention_html()}\n"
                f"📝 Нарушений: {violation_count}\n"
                f"🔢 Предупреждений: <b>{warn_count}/3</b>\n\n"
                f"⚠️ При достижении 3 предупреждений - бан!"
            )
            
            warning_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=warning_msg_text,
                parse_mode='HTML'
            )
            
            await asyncio.sleep(5)
            try:
                await warning_msg.delete()
            except:
                pass
            
            # Автобан при 3 предупреждениях
            if warn_count >= 3:
                try:
                    await context.bot.ban_chat_member(update.effective_chat.id, int(user_id))
                    ban_text = (
                        f"🔨 <b>АВТОБАН ЗА ССЫЛКИ</b>\n\n"
                        f"👤 Пользователь: {message.from_user.mention_html()}\n"
                        f"📝 Причина: Накоплено 3 предупреждения за отправку ссылок"
                    )
                    await send_auto_delete_message(context, update.effective_chat.id, ban_text)
                except Exception as e:
                    print(f"Ошибка автобана: {e}")
        except Exception as e:
            print(f"Ошибка обработки ссылок: {e}")

# --- СТАТИСТИКА ---
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /top - топ воркеров"""
    if not await check_command_spam(update, context, "top", cooldown_seconds=5):
        return
    
    command = update.message.text.split()[0][1:]
    period = "месяц" if command == "topm" else ("день" if command == "topd" else "все время")
    
    message = (
        f"📊 <b>ТОП ВОРКЕРОВ ЗА {period.upper()}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <i>Функция в разработке</i>\n\n"
        f"📈 Здесь будет отображаться:\n"
        f"• Топ воркеров по профитам\n"
        f"• Количество профитов\n"
        f"• Общая сумма\n"
        f"• Средний профит\n\n"
        f"🚀 Скоро будет доступна полная статистика!"
    )
    
    sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message, countdown=15)
    if sent_msg:
        if "last_bot_messages" not in bot_data:
            bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_msg.chat.id,
            'message_id': sent_msg.message_id
        }
        save_data()

async def mp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mp - личный кабинет воркера"""
    print(f"🔔 Вызвана команда /mp от пользователя {update.effective_user.id}")
    
    if not await check_command_spam(update, context, "mp", cooldown_seconds=5):
        print(f"⏳ Команда /mp заблокирована антиспамом для пользователя {update.effective_user.id}")
        return
    
    print(f"✅ Антиспам пройден, выполняю команду /mp")
    
    user = update.effective_user
    user_id = str(user.id)
    
    if "workers" not in bot_data:
        bot_data["workers"] = {}
    
    if user_id not in bot_data["workers"]:
        bot_data["workers"][user_id] = {
            "tag": user.username or "Аноним",
            "profits_day": 0,
            "profits_month": 0,
            "total": 0,
            "mammoths_count": 0
        }
        save_data()
    
    worker = bot_data["workers"][user_id]
    
    message = (
        f"👤 <b>ЛИЧНЫЙ КАБИНЕТ ВОРКЕРА</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷 <b>Тег:</b> @{worker['tag']}\n"
        f"📊 <b>Статус:</b> Воркер\n"
        f"🦣 <b>Мамонтов:</b> {worker.get('mammoths_count', 0)}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <i>Функция в разработке</i>\n\n"
        f"📈 Здесь будет отображаться:\n"
        f"• Статистика за день/месяц\n"
        f"• Общее количество профитов\n"
        f"• Среднее количество профитов\n"
        f"• График активности\n\n"
        f"🚀 Скоро будет доступна полная статистика!"
    )
    
    sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message, countdown=15)
    if sent_msg:
        if "last_bot_messages" not in bot_data:
            bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_msg.chat.id,
            'message_id': sent_msg.message_id
        }
        save_data()

# --- ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ---
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ping - упоминает всех пользователей"""
    if not await is_admin(update, context):
        return
    
    if not await check_command_spam(update, context, "ping", cooldown_seconds=10):
        return
    
    try:
        chat_id = update.effective_chat.id
        
        if "users" not in bot_data:
            bot_data["users"] = {}
            save_data()
        
        mentions = []
        for user_id, user_info in bot_data["users"].items():
            if user_info.get("username"):
                mentions.append(f"@{user_info['username']}")
            else:
                mentions.append(f"<a href='tg://user?id={user_id}'>{user_info.get('first_name', 'User')}</a>")
        
        if not mentions:
            message_text = (
                "ℹ️ <b>ИНФОРМАЦИЯ</b>\n\n"
                "Нет сохраненных пользователей.\n"
                "Пользователи появятся после их активности в чате."
            )
            await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=5)
            return
        
        # Разбиваем на группы по 5 пользователей
        chunk_size = 5
        mention_chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
        
        message_text = f"📢 <b>PING ВСЕХ УЧАСТНИКОВ</b>\n\n"
        for chunk in mention_chunks:
            message_text += " ".join(chunk) + "\n"
        
        message_text += f"\n👥 <b>Всего: {len(mentions)} пользователей</b>"
        
        sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=15)
        if sent_msg:
            if "last_bot_messages" not in bot_data:
                bot_data["last_bot_messages"] = {}
            bot_data["last_bot_messages"][str(update.effective_user.id)] = {
                'chat_id': sent_msg.chat.id,
                'message_id': sent_msg.message_id
            }
            save_data()
    except Exception as e:
        print(f"Ошибка в ping_command: {e}")

async def manuals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /manuals - отправляет ссылку на мануалы"""
    if not await check_command_spam(update, context, "manuals", cooldown_seconds=5):
        return
    
    try:
        keyboard = [
            [InlineKeyboardButton("📖 Читать мануалы", url="https://telegra.ph/MANUAL-NARKO--DECEPTION-TEAM-12-08")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            "📚 <b>МАНУАЛЫ ДЛЯ РАБОТЫ</b>\n\n"
            "Для прочтения мануалов по работе нажмите на кнопку ниже 👇\n\n"
            "⏱ <i>Удаление через: 10 сек</i>"
        )
        
        sent_message = await update.message.reply_text(
            text=message_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        if "last_bot_messages" not in bot_data:
            bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_message.chat.id,
            'message_id': sent_message.message_id
        }
        save_data()

        async def manuals_countdown():
            for remaining in range(9, 0, -1):
                await asyncio.sleep(1)
                updated_text = (
                    "📚 <b>МАНУАЛЫ ДЛЯ РАБОТЫ</b>\n\n"
                    "Для прочтения мануалов по работе нажмите на кнопку ниже 👇\n\n"
                    f"⏱ <i>Удаление через: {remaining} сек</i>"
                )
                try:
                    await sent_message.edit_text(
                        text=updated_text,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                except Exception:
                    pass
            
            await asyncio.sleep(1)
            try:
                await sent_message.delete()
            except:
                pass

        asyncio.create_task(manuals_countdown())
        
    except Exception as e:
        print(f"Ошибка в manuals_command: {e}")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /info - показывает доступные команды"""
    print(f"🔔 Вызвана команда /info от пользователя {update.effective_user.id}")
    
    if not await check_command_spam(update, context, "info", cooldown_seconds=5):
        print(f"⏳ Команда /info заблокирована антиспамом для пользователя {update.effective_user.id}")
        return
    
    print(f"✅ Антиспам пройден, выполняю команду /info")
    
    try:
        message_text = (
            "ℹ️ <b>ДОСТУПНЫЕ КОМАНДЫ</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📋 <b>Основные команды:</b>\n"
            "• /info - показать это сообщение\n"
            "• /manuals - мануалы для работы\n\n"
            "📊 <b>Статистика:</b>\n"
            "• /top - топ воркеров (общий)\n"
            "• /topd - топ воркеров (за день)\n"
            "• /topm - топ воркеров (за месяц)\n"
            "• /mp - личный кабинет\n\n"
            "👮 <b>Модерация (только для админов):</b>\n"
            "• /mute [время] [причина] - замутить\n"
            "• /unmute - размутить\n"
            "• /ban [время] [причина] - забанить\n"
            "• /unban - разбанить\n"
            "• /kick [причина] - кикнуть\n"
            "• /kicku @user1 @user2 - массовый кик\n"
            "• /warn [причина] - предупреждение\n"
            "• /unwarn - снять предупреждение\n"
            "• /ping - упомянуть всех\n"
            "• /card - показать карту\n\n"
            "⏱ <i>Удаление через: 5:00</i>"
        )
        
        sent_message = await update.message.reply_text(
            text=message_text,
            parse_mode='HTML'
        )
        
        if "last_bot_messages" not in bot_data:
            bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_message.chat.id,
            'message_id': sent_message.message_id
        }
        save_data()

        async def info_countdown():
            end_time = datetime.now() + timedelta(seconds=300)
            
            while True:
                now = datetime.now()
                if now >= end_time:
                    break
                
                remaining = int((end_time - now).total_seconds())
                minutes = remaining // 60
                seconds = remaining % 60
                time_str = f"{minutes}:{seconds:02d}"
                
                updated_text = (
                    "ℹ️ <b>ДОСТУПНЫЕ КОМАНДЫ</b>\n\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    "📋 <b>Основные команды:</b>\n"
                    "• /info - показать это сообщение\n"
                    "• /manuals - мануалы для работы\n\n"
                    "📊 <b>Статистика:</b>\n"
                    "• /top - топ воркеров (общий)\n"
                    "• /topd - топ воркеров (за день)\n"
                    "• /topm - топ воркеров (за месяц)\n"
                    "• /mp - личный кабинет\n\n"
                    "👮 <b>Модерация (только для админов):</b>\n"
                    "• /mute [время] [причина] - замутить\n"
                    "• /unmute - размутить\n"
                    "• /ban [время] [причина] - забанить\n"
                    "• /unban - разбанить\n"
                    "• /kick [причина] - кикнуть\n"
                    "• /kicku @user1 @user2 - массовый кик\n"
                    "• /warn [причина] - предупреждение\n"
                    "• /unwarn - снять предупреждение\n"
                    "• /ping - упомянуть всех\n"
                    "• /card [номер] [банк] - показать карту (с автоудалением)\n\n"
                    f"⏱ <i>Удаление через: {time_str}</i>"
                )
                
                try:
                    await sent_message.edit_text(
                        text=updated_text,
                        parse_mode='HTML'
                    )
                except Exception:
                    pass
                    
                await asyncio.sleep(1)
            
            await asyncio.sleep(1)
            try:
                await sent_message.delete()
            except:
                pass

        asyncio.create_task(info_countdown())
        
    except Exception as e:
        print(f"Ошибка в info_command: {e}")

async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /card - показать информацию о карте с таймером"""
    print(f"🔔 Вызвана команда /card от пользователя {update.effective_user.id}")
    
    if not await check_command_spam(update, context, "card", cooldown_seconds=15):
        print(f"⏳ Команда /card заблокирована антиспамом для пользователя {update.effective_user.id}")
        return

    print(f"✅ Антиспам пройден, выполняю команду /card")
    try:
        user_is_admin = await is_admin(update, context)
        print(f"👤 Пользователь ID: {update.effective_user.id}, Username: {update.effective_user.username}")
        print(f"👮 Является админом: {user_is_admin}")
        print(f"📝 Аргументы команды: {context.args}")
        updated = False

        # Админ может обновить реквизиты через аргументы
        if user_is_admin and context.args:
            print(f"✏️ Админ обновляет реквизиты: {context.args}")
            raw_number = context.args[0]
            bank_name = " ".join(context.args[1:]).strip() if len(context.args) > 1 else ""
            
            # Обработка сброса реквизитов: /card - -
            if raw_number == "-" and (bank_name == "-" or bank_name == ""):
                formatted_number = DEFAULT_CARD_NUMBER
                bank_name = DEFAULT_CARD_BANK
                print(f"🔄 Сброс реквизитов на значения по умолчанию")
            else:
                # Если банк не указан, используем текущий или дефолтный
                if not bank_name:
                    bank_name = bot_data.get("card_bank", DEFAULT_CARD_BANK)
                
                # Форматируем номер (4400 0000 0000 0000)
                card_digits = raw_number.replace(" ", "")
                if len(card_digits) == 16 and card_digits.isdigit():
                    formatted_number = " ".join([card_digits[i:i+4] for i in range(0, 16, 4)])
                else:
                    formatted_number = raw_number

            bot_data["card_number"] = formatted_number
            bot_data["card_bank"] = bank_name
            save_data()
            updated = True
            print(f"💾 Реквизиты обновлены: Карта={formatted_number}, Банк={bank_name}")
            
            # Отправляем уведомление в группу о новых реквизитах
            try:
                notification_chat_id = -1003608461364
                notification_text = (
                    "💳 <b>НОВЫЕ РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"
                    f"🏦 <b>Банк:</b> <code>{html.escape(bank_name)}</code>\n"
                    f"💳 <b>Карта:</b> <code>{html.escape(formatted_number)}</code>\n\n"
                    "💰 <b>Для прямых переводов:</b> 80%\n"
                    "🤝 <b>Через ТП:</b> 70%\n\n"
                    "✨ <b>ЖЕЛАЕМ ЛУЧШИХ ПРОФИТОВ!</b> ✨"
                )
                await context.bot.send_message(
                    chat_id=notification_chat_id,
                    text=notification_text,
                    parse_mode='HTML'
                )
                print(f"📢 Уведомление отправлено в группу {notification_chat_id}")
            except Exception as e:
                print(f"⚠️ Ошибка отправки уведомления в группу: {e}")
            
            # Удаляем команду админа, чтобы не светить реквизиты в чате
            try:
                await update.message.delete()
            except Exception:
                pass
        elif context.args and not user_is_admin:
            print(f"⛔ Пользователь попытался обновить реквизиты, но не является админом")

        # Показать текущую карту всем (без аргументов или после обновления)
        card_number = str(bot_data.get("card_number", DEFAULT_CARD_NUMBER) or DEFAULT_CARD_NUMBER)
        bank_name = str(bot_data.get("card_bank", DEFAULT_CARD_BANK) or DEFAULT_CARD_BANK)
        safe_card = html.escape(card_number)
        safe_bank = html.escape(bank_name)

        # Формируем текст сообщения
        update_prefix = "✅ <b>Реквизиты обновлены</b>\n\n" if updated else ""
        message_text = (
            f"{update_prefix}"
            "💳 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"
            "💰 <b>Для прямых переводов:</b> 80%\n"
            "🤝 <b>Через ТП:</b> 70%\n\n"
            f"🏦 <b>Банк:</b> <code>{safe_bank}</code>\n"
            f"💳 <b>Карта:</b> <code>{safe_card}</code>\n\n"
            "⏱ <i>Удаление через: 60 сек</i>"
        )

        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode='HTML'
        )

        # Сохраняем ID команды пользователя для удаления (если она еще не удалена)
        # Команда админа удаляется сразу при обновлении реквизитов, поэтому не удаляем ее повторно
        user_command_message_id = None
        if update.message and not (updated and user_is_admin):
            user_command_message_id = update.message.message_id

        # Обратный отсчет и автоудаление
        async def card_countdown():
            for remaining in range(59, 0, -1):
                await asyncio.sleep(1)
                updated_text = (
                    f"{update_prefix}"
                    "💳 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"
                    "💰 <b>Для прямых переводов:</b> 80%\n"
                    "🤝 <b>Через ТП:</b> 70%\n\n"
                    f"🏦 <b>Банк:</b> <code>{safe_bank}</code>\n"
                    f"💳 <b>Карта:</b> <code>{safe_card}</code>\n\n"
                    f"⏱ <i>Удаление через: {remaining} сек</i>"
                )
                try:
                    await sent_message.edit_text(
                        text=updated_text,
                        parse_mode='HTML'
                    )
                except Exception:
                    pass
            await asyncio.sleep(1)
            try:
                # Удаляем сообщение бота
                await sent_message.delete()
                # Удаляем команду пользователя (если она еще не удалена)
                if user_command_message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id,
                            message_id=user_command_message_id
                        )
                    except Exception:
                        pass
            except Exception:
                pass

        asyncio.create_task(card_countdown())

    except Exception as e:
        print(f"Ошибка в card_command: {e}")
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось показать карту:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /myid - показать свой ID"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Нет username"
    first_name = update.effective_user.first_name or ""
    
    is_in_admin_list = user_id in ADMIN_IDS
    user_is_admin = await is_admin(update, context)
    
    message_text = (
        f"🆔 <b>ВАША ИНФОРМАЦИЯ</b>\n\n"
        f"👤 Имя: {html.escape(first_name)}\n"
        f"📱 Username: @{html.escape(username)}\n"
        f"🔢 ID: <code>{user_id}</code>\n\n"
        f"{'✅' if is_in_admin_list else '❌'} В списке ADMIN_IDS: {is_in_admin_list}\n"
        f"{'✅' if user_is_admin else '❌'} Админ в чате: {user_is_admin}\n\n"
        f"💡 Для добавления в админы бота добавьте ваш ID в ADMIN_IDS"
    )
    
    await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=15)

async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /warns - показать предупреждения пользователя"""
    if not await check_command_spam(update, context, "warns", cooldown_seconds=5):
        return
    
    if not update.message.reply_to_message:
        # Показываем свои предупреждения
        user_id = str(update.effective_user.id)
    else:
        # Показываем предупреждения ответленного пользователя
        if not await is_admin(update, context):
            await send_auto_delete_message(
                context, update.effective_chat.id,
                "❌ <b>ОШИБКА</b>\n\nТолько администраторы могут просматривать предупреждения других пользователей!",
                countdown=5
            )
            return
        user_id = str(update.message.reply_to_message.from_user.id)
        user = update.message.reply_to_message.from_user
    
    if "warns" not in bot_data or user_id not in bot_data["warns"] or not bot_data["warns"][user_id]:
        message_text = (
            f"✅ <b>ПРЕДУПРЕЖДЕНИЙ НЕТ</b>\n\n"
            f"👤 Пользователь: {user.mention_html() if update.message.reply_to_message else update.effective_user.mention_html()}\n"
            f"✅ У пользователя нет предупреждений"
        )
    else:
        warns = bot_data["warns"][user_id]
        warn_count = len(warns)
        
        message_text = (
            f"⚠️ <b>ПРЕДУПРЕЖДЕНИЯ</b>\n\n"
            f"👤 Пользователь: {user.mention_html() if update.message.reply_to_message else update.effective_user.mention_html()}\n"
            f"🔢 Всего: <b>{warn_count}/3</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        for idx, warn in enumerate(warns[-5:], 1):  # Показываем последние 5
            warn_date = datetime.fromisoformat(warn["date"]).strftime('%d.%m.%Y %H:%M')
            admin_name = warn.get("admin", "Система")
            message_text += (
                f"<b>{idx}.</b> {warn['reason']}\n"
                f"👮 Админ: {admin_name}\n"
                f"⏰ {warn_date}\n\n"
            )
        
        if warn_count > 5:
            message_text += f"... и еще {warn_count - 5} предупреждений\n\n"
    
    await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=10)

# --- КОМАНДА /PROFIT ---
async def generate_profit_image(worker_tag: str, direction: str, amount: str, image_urls: list = None) -> str:
    """Генерирует изображение профита через API с повторными попытками
    
    Args:
        worker_tag: Тэг воркера
        direction: Направление (НАРКО или ПРЯМОЙ ПЕРЕВОД)
        amount: Сумма профита
        image_urls: Список URL изображений для редактирования (опционально, максимум 8)
    """
    prompt = f"""Epic, ultra-dark, minimalist esports-style graphic design.

Square format 16:9.

Black matte background with deep shadows and subtle gradients.

In the center — stylized mammoth logo, powerful and intimidating silhouette, sharp angular lines, minimal details, modern vector design. The mammoth looks massive, dominant, and elite.

Overall style: mysterious, sleek, premium, high-contrast, dark tones only (black, deep gray, dark graphite). Dramatic cinematic lighting, soft rim light, realistic shadows.

Text is placed cleanly and symmetrically, using modern bold sans-serif font, perfectly readable, no distortions, no artifacts.

Replace all emojis with glass-style icons (glassmorphism) — transparent, glossy, crystal-like UI icons with soft reflections and subtle glow.

Text content:
At the very top there is a large text Glass scam icon + text: НОВЫЙ ПРОФИТ (size text 67) 
(size text 60) Glass diamond icon + text: ВОРКЕР: {worker_tag}
(size text 60) NARCOS icon + text: НАПРАВЛЕНИЕ: {direction}
(size text 60) money icon + text: Сумма оплаты: {amount}

No bright colors, no neon, no gradients outside dark palette.
No cartoon style, no cheap effects, no visible AI artifacts.
The font should be clear, the font design should be visible normally on the entire design.
Premium esports branding, looks expensive, elite, intimidating.
Designed to look perfect as a logo/post even at small sizes.
Ultra-clean, ultra-sharp, professional graphic design
16:9."""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "nano-banana-pro",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
        "aspectRatio": "16:9",
        "resolution": "1k"
    }
    
    # Добавляем URL изображений для редактирования, если они переданы
    if image_urls and len(image_urls) > 0:
        # Ограничиваем максимум 8 изображений
        image_urls = image_urls[:8]
        payload["image_urls"] = image_urls
        print(f"🖼 Используется {len(image_urls)} изображение(й) для редактирования")
    
    attempt = 0
    max_attempts = 300  # Максимум 5 минут (300 секунд)
    
    print(f"🚀 Начинаю генерацию изображения через API: {API_URL}")
    
    # Отправляем запросы каждую секунду до получения успешного ответа
    while attempt < max_attempts:
        attempt += 1
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            # Пытаемся распарсить ответ
            try:
                result = response.json()
                # Логируем только при ошибках или успехе
                if response.status_code != 200:
                    print(f"📡 Попытка {attempt}: Status {response.status_code}")
                    print(f"📦 Ответ API: {json.dumps(result, ensure_ascii=False)[:200]}...")
            except Exception as e:
                result = None
                print(f"⚠️ Не удалось распарсить JSON (попытка {attempt}): {e}")
                print(f"📄 Текст ответа: {response.text[:200]}")
            
            # Проверяем на наличие ошибок в теле ответа
            error_message = None
            wait_time = None
            
            if isinstance(result, dict):
                # Проверяем на сообщения об ошибках
                if "error" in result:
                    error_obj = result["error"]
                    if isinstance(error_obj, dict):
                        error_message = error_obj.get("message", str(error_obj))
                    else:
                        error_message = str(error_obj)
                elif "message" in result:
                    error_message = str(result["message"])
                
                # Извлекаем время ожидания из сообщения
                if error_message and "try again in" in error_message.lower():
                    match = re.search(r'try again in ([\d.]+) seconds?', error_message.lower())
                    if match:
                        wait_time = float(match.group(1))
                        # API ограничивает до 1 запроса в секунду, поэтому ждем минимум 1.2 секунды
                        # Добавляем небольшую случайную задержку для избежания конфликтов
                        import random
                        wait_time = max(wait_time, 1.2) + random.uniform(0.1, 0.3)
            
            # Если есть сообщение об ошибке rate limit
            if error_message and ("rate limit" in error_message.lower() or "try again" in error_message.lower()):
                if wait_time:
                    # Логируем только каждую 5-ю попытку, чтобы не спамить
                    if attempt % 5 == 0 or attempt <= 3:
                        print(f"⚠️ Rate limit (попытка {attempt}), ждем {wait_time:.2f} сек...")
                    await asyncio.sleep(wait_time)
                else:
                    # Если не удалось извлечь время, ждем 1.5 секунды
                    import random
                    wait_time = 1.5 + random.uniform(0.1, 0.3)
                    if attempt % 5 == 0 or attempt <= 3:
                        print(f"⚠️ Rate limit (попытка {attempt}), ждем {wait_time:.2f} сек...")
                    await asyncio.sleep(wait_time)
                continue
            
            # Проверяем успешный ответ
            if response.status_code == 200:
                if isinstance(result, dict):
                    # Проверяем разные возможные структуры ответа
                    if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
                        image_url = result["data"][0].get("url")
                        if image_url:
                            print(f"✅ Изображение успешно сгенерировано за {attempt} попыток")
                            print(f"🖼 URL изображения: {image_url}")
                            return image_url
                    # Может быть другой формат ответа
                    if "url" in result:
                        image_url = result["url"]
                        print(f"✅ Изображение успешно сгенерировано за {attempt} попыток")
                        print(f"🖼 URL изображения: {image_url}")
                        return image_url
                    if "image" in result:
                        image_url = result["image"]
                        print(f"✅ Изображение успешно сгенерировано за {attempt} попыток")
                        print(f"🖼 URL изображения: {image_url}")
                        return image_url
                elif isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict) and "url" in result[0]:
                        image_url = result[0]["url"]
                        print(f"✅ Изображение успешно сгенерировано за {attempt} попыток")
                        print(f"🖼 URL изображения: {image_url}")
                        return image_url
                
                # Если есть ошибка в ответе
                if error_message:
                    print(f"⚠️ Ошибка в ответе 200 (попытка {attempt}): {error_message}")
                else:
                    print(f"⚠️ Получен ответ 200, но нет URL (попытка {attempt})")
                    print(f"📋 Структура ответа: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            elif response.status_code == 429:  # Rate limit
                # Если не извлекли время из сообщения, извлекаем из ответа
                if not wait_time and isinstance(result, dict) and "error" in result:
                    error_obj = result["error"]
                    if isinstance(error_obj, dict):
                        error_msg = error_obj.get("message", "")
                        if "try again in" in error_msg.lower():
                            match = re.search(r'try again in ([\d.]+) seconds?', error_msg.lower())
                            if match:
                                wait_time = float(match.group(1))
                                import random
                                wait_time = max(wait_time, 1.2) + random.uniform(0.1, 0.3)
                
                if wait_time:
                    # Логируем только каждую 5-ю попытку
                    if attempt % 5 == 0 or attempt <= 3:
                        print(f"⚠️ Rate limit 429 (попытка {attempt}), ждем {wait_time:.2f} сек...")
                    await asyncio.sleep(wait_time)
                else:
                    # Если не удалось извлечь время, ждем 1.5 секунды
                    import random
                    wait_time = 1.5 + random.uniform(0.1, 0.3)
                    if attempt % 5 == 0 or attempt <= 3:
                        print(f"⚠️ Rate limit 429 (попытка {attempt}), ждем {wait_time:.2f} сек...")
                    await asyncio.sleep(wait_time)
                continue
            else:
                error_text = error_message or f"Status {response.status_code}"
                print(f"⚠️ Ошибка API (попытка {attempt}): {error_text}")
                if result:
                    print(f"📋 Детали ошибки: {result}")
            
        except requests.exceptions.Timeout:
            # Логируем только каждую 10-ю попытку
            if attempt % 10 == 0 or attempt <= 3:
                print(f"⚠️ Timeout (попытка {attempt}), продолжаем...")
            # При timeout ждем 1.5 секунды
            import random
            await asyncio.sleep(1.5 + random.uniform(0.1, 0.3))
        except requests.exceptions.ConnectionError as e:
            if attempt % 10 == 0 or attempt <= 3:
                print(f"⚠️ Ошибка подключения (попытка {attempt}): {e}")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Ошибка запроса (попытка {attempt}): {e}")
            import traceback
            traceback.print_exc()
            # При ошибке ждем 1.5 секунды
            import random
            await asyncio.sleep(1.5 + random.uniform(0.1, 0.3))
    
    raise Exception(f"Не удалось сгенерировать изображение за {max_attempts} попыток")

async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profit - создание поста о профите (только ЛС, только админы)"""
    # Проверка что это личное сообщение
    if update.effective_chat.type != "private":
        return  # Молча игнорируем в группах
    
    # Проверка прав администратора
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ <b>ДОСТУП ЗАПРЕЩЕН</b>\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode='HTML'
        )
        return
    
    # Инициализация состояния для пользователя
    user_id = str(update.effective_user.id)
    if "profit_states" not in bot_data:
        bot_data["profit_states"] = {}
    
    bot_data["profit_states"][user_id] = {
        "step": "worker_tag",
        "worker_tag": None,
        "direction": None,
        "amount": None,
        "image_urls": []  # Список URL изображений для редактирования
    }
    save_data()
    
    await update.message.reply_text(
        "💼 <b>СОЗДАНИЕ ПОСТА О ПРОФИТЕ</b>\n\n"
        "📝 <b>Шаг 1/3:</b> Введите тэг воркера\n\n"
        "Пример: <code>@username</code> или <code>username</code>",
        parse_mode='HTML'
    )

async def handle_profit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода данных для команды /profit"""
    # Проверка что это личное сообщение
    if update.effective_chat.type != "private":
        return
    
    user_id = str(update.effective_user.id)
    
    # Проверяем что пользователь в процессе создания профита
    if "profit_states" not in bot_data or user_id not in bot_data["profit_states"]:
        return
    
    state = bot_data["profit_states"][user_id]
    step = state["step"]
    text = update.message.text.strip()
    
    if step == "worker_tag":
        # Сохраняем тэг воркера
        worker_tag = text.lstrip('@')
        state["worker_tag"] = worker_tag
        state["step"] = "direction"
        save_data()
        
        await update.message.reply_text(
            "💼 <b>СОЗДАНИЕ ПОСТА О ПРОФИТЕ</b>\n\n"
            "📝 <b>Шаг 2/3:</b> Введите направление\n\n"
            "Варианты:\n"
            "• <code>НАРКО</code>\n"
            "• <code>ПРЯМОЙ ПЕРЕВОД</code>",
            parse_mode='HTML'
        )
    
    elif step == "direction":
        # Проверяем и сохраняем направление
        direction_upper = text.upper()
        if "НАРКО" in direction_upper:
            direction = "НАРКО"
        elif "ПРЯМОЙ" in direction_upper or "ПЕРЕВОД" in direction_upper:
            direction = "ПРЯМОЙ ПЕРЕВОД"
        else:
            await update.message.reply_text(
                "❌ <b>ОШИБКА</b>\n\n"
                "Пожалуйста, введите одно из направлений:\n"
                "• <code>НАРКО</code>\n"
                "• <code>ПРЯМОЙ ПЕРЕВОД</code>",
                parse_mode='HTML'
            )
            return
        
        state["direction"] = direction
        state["step"] = "amount"
        save_data()
        
        await update.message.reply_text(
            "💼 <b>СОЗДАНИЕ ПОСТА О ПРОФИТЕ</b>\n\n"
            "📝 <b>Шаг 3/3:</b> Введите сумму профита\n\n"
            "Пример: <code>50000</code> или <code>50 000</code>",
            parse_mode='HTML'
        )
    
    elif step == "amount":
        # Сохраняем сумму и переходим к опциональной загрузке изображения
        amount = text
        state["amount"] = amount
        state["step"] = "image_optional"
        save_data()
        
        await update.message.reply_text(
            "💼 <b>СОЗДАНИЕ ПОСТА О ПРОФИТЕ</b>\n\n"
            "📝 <b>Шаг 4/4 (опционально):</b> Загрузите изображение для редактирования\n\n"
            "Вы можете:\n"
            "• Отправить изображение (фото)\n"
            "• Отправить URL изображения (ссылку)\n"
            "• Написать <code>пропустить</code> или <code>нет</code> для генерации с нуля\n\n"
            "Максимум 8 изображений",
            parse_mode='HTML'
        )
    
    elif step == "image_optional":
        # Обработка опционального изображения
        if text.lower() in ["пропустить", "нет", "skip", "no", ""]:
            # Пропускаем загрузку изображения, начинаем генерацию
            state["step"] = "generating"
            save_data()
            
            await _start_image_generation(update, context, state, user_id)
        elif text.lower() in ["готово", "done", "start", "начать"]:
            # Начинаем генерацию с уже добавленными изображениями
            if len(state["image_urls"]) == 0:
                await update.message.reply_text(
                    "⚠️ <b>Нет изображений</b>\n\n"
                    "Вы не добавили изображений. Напишите <code>пропустить</code> для генерации с нуля",
                    parse_mode='HTML'
                )
                return
            
            state["step"] = "generating"
            save_data()
            
            await _start_image_generation(update, context, state, user_id)
        else:
            # Проверяем, является ли текст URL
            if text.startswith(("http://", "https://")):
                # Это URL изображения
                if len(state["image_urls"]) < 8:
                    state["image_urls"].append(text)
                    save_data()
                    
                    await update.message.reply_text(
                        f"✅ <b>Изображение добавлено</b>\n\n"
                        f"Добавлено изображений: {len(state['image_urls'])}/8\n\n"
                        "Отправьте еще изображение или URL, или напишите <code>готово</code> для начала генерации",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        "❌ <b>Достигнут лимит</b>\n\n"
                        "Максимум 8 изображений. Напишите <code>готово</code> для начала генерации",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ <b>ОШИБКА</b>\n\n"
                    "Пожалуйста, отправьте:\n"
                    "• Изображение (фото)\n"
                    "• URL изображения (начинается с http:// или https://)\n"
                    "• <code>пропустить</code> для генерации с нуля\n"
                    "• <code>готово</code> для начала генерации",
                    parse_mode='HTML'
                )
    
    elif step == "generating":
        # Игнорируем сообщения во время генерации
        return

async def _start_image_generation(update, context, state, user_id):
    """Запускает процесс генерации изображения"""
    # Отправляем сообщение о генерации
    status_msg = await update.message.reply_text(
        "⏳ <b>ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ</b>\n\n"
        "Пожалуйста, подождите...",
        parse_mode='HTML'
    )
    
    try:
        # Генерируем изображение
        image_url = await generate_profit_image(
            state["worker_tag"],
            state["direction"],
            state["amount"],
            state["image_urls"] if state["image_urls"] else None
        )
        
        state["generated_image_url"] = image_url
        state["step"] = "ready"
        save_data()
        
        # Удаляем сообщение о генерации
        try:
            await status_msg.delete()
        except:
            pass
        
        # Отправляем изображение с кнопками
        caption = (
            "💼 <b>НОВЫЙ ПРОФИТ!</b>\n\n"
            f"👤 <b>Воркер:</b> {html.escape(state['worker_tag'])}\n"
            f"📋 <b>Направление:</b> {html.escape(state['direction'])}\n"
            f"💰 <b>Сумма:</b> {html.escape(state['amount'])}\n\n"
            "✨ <b>ЖЕЛАЕМ ЛУЧШИХ ПРОФИТОВ!</b> ✨"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"profit_confirm_{user_id}"),
                InlineKeyboardButton("🔄 Переделать", callback_data=f"profit_redo_{user_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=image_url,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        print(f"Ошибка генерации изображения: {e}")
        try:
            await status_msg.delete()
        except:
            pass
        await update.message.reply_text(
            f"❌ <b>ОШИБКА</b>\n\n"
            f"Не удалось сгенерировать изображение:\n{str(e)}\n\n"
            "Попробуйте еще раз командой /profit",
            parse_mode='HTML'
        )
        # Очищаем состояние
        if user_id in bot_data["profit_states"]:
            del bot_data["profit_states"][user_id]
            save_data()

async def handle_profit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженных изображений для команды /profit"""
    # Проверка что это личное сообщение
    if update.effective_chat.type != "private":
        return
    
    user_id = str(update.effective_user.id)
    
    # Проверяем что пользователь в процессе создания профита
    if "profit_states" not in bot_data or user_id not in bot_data["profit_states"]:
        return
    
    state = bot_data["profit_states"][user_id]
    
    # Проверяем, что мы на этапе загрузки изображений
    if state["step"] != "image_optional":
        return
    
    # Получаем URL изображения
    photo = update.message.photo[-1] if update.message.photo else None
    if not photo:
        await update.message.reply_text(
            "❌ <b>ОШИБКА</b>\n\n"
            "Не удалось получить изображение. Попробуйте еще раз.",
            parse_mode='HTML'
        )
        return
    
    # Получаем файл и его URL
    try:
        file = await context.bot.get_file(photo.file_id)
        image_url = file.file_path
        
        # Добавляем полный URL если нужно
        if not image_url.startswith("http"):
            image_url = f"https://api.telegram.org/file/bot{context.bot.token}/{image_url}"
        
        if len(state["image_urls"]) < 8:
            state["image_urls"].append(image_url)
            save_data()
            
            await update.message.reply_text(
                f"✅ <b>Изображение добавлено</b>\n\n"
                f"Добавлено изображений: {len(state['image_urls'])}/8\n\n"
                "Отправьте еще изображение или URL, или напишите <code>готово</code> для начала генерации",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ <b>Достигнут лимит</b>\n\n"
                "Максимум 8 изображений. Напишите <code>готово</code> для начала генерации",
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")
        await update.message.reply_text(
            f"❌ <b>ОШИБКА</b>\n\n"
            f"Не удалось обработать изображение:\n{str(e)}",
            parse_mode='HTML'
        )

async def handle_profit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов от кнопок команды /profit"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    if data.startswith("profit_confirm_"):
        # Подтверждение - отправляем в группу
        target_user_id = data.replace("profit_confirm_", "")
        
        if user_id != target_user_id:
            await query.answer("❌ Это не ваш пост!", show_alert=True)
            return
        
        if "profit_states" not in bot_data or target_user_id not in bot_data["profit_states"]:
            await query.answer("❌ Данные не найдены!", show_alert=True)
            return
        
        state = bot_data["profit_states"][target_user_id]
        
        if not state.get("generated_image_url"):
            await query.answer("❌ Изображение не найдено!", show_alert=True)
            return
        
        try:
            # Отправляем в группу
            caption = (
                "💼 <b>НОВЫЙ ПРОФИТ!</b>\n\n"
                f"👤 <b>Воркер:</b> {html.escape(state['worker_tag'])}\n"
                f"📋 <b>Направление:</b> {html.escape(state['direction'])}\n"
                f"💰 <b>Сумма:</b> {html.escape(state['amount'])}\n\n"
                "✨ <b>ЖЕЛАЕМ ЛУЧШИХ ПРОФИТОВ!</b> ✨"
            )
            
            await context.bot.send_photo(
                chat_id=PROFIT_GROUP_ID,
                photo=state["generated_image_url"],
                caption=caption,
                parse_mode='HTML'
            )
            
            await query.edit_message_caption(
                caption=caption + "\n\n✅ <b>Отправлено в группу!</b>",
                parse_mode='HTML'
            )
            
            # Очищаем состояние
            del bot_data["profit_states"][target_user_id]
            save_data()
            
        except Exception as e:
            print(f"Ошибка отправки в группу: {e}")
            await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    
    elif data.startswith("profit_redo_"):
        # Переделка - генерируем новое изображение
        target_user_id = data.replace("profit_redo_", "")
        
        if user_id != target_user_id:
            await query.answer("❌ Это не ваш пост!", show_alert=True)
            return
        
        if "profit_states" not in bot_data or target_user_id not in bot_data["profit_states"]:
            await query.answer("❌ Данные не найдены!", show_alert=True)
            return
        
        state = bot_data["profit_states"][target_user_id]
        state["step"] = "generating"
        state["generated_image_url"] = None
        save_data()
        
        # Обновляем сообщение
        await query.edit_message_caption(
            caption="⏳ <b>ГЕНЕРАЦИЯ НОВОГО ИЗОБРАЖЕНИЯ</b>\n\nПожалуйста, подождите...",
            parse_mode='HTML'
        )
        
        try:
            # Генерируем новое изображение (используем те же image_urls если они есть)
            image_url = await generate_profit_image(
                state["worker_tag"],
                state["direction"],
                state["amount"],
                state["image_urls"] if state["image_urls"] else None
            )
            
            state["generated_image_url"] = image_url
            state["step"] = "ready"
            save_data()
            
            # Отправляем новое изображение
            caption = (
                "💼 <b>НОВЫЙ ПРОФИТ!</b>\n\n"
                f"👤 <b>Воркер:</b> {html.escape(state['worker_tag'])}\n"
                f"📋 <b>Направление:</b> {html.escape(state['direction'])}\n"
                f"💰 <b>Сумма:</b> {html.escape(state['amount'])}\n\n"
                "✨ <b>ЖЕЛАЕМ ЛУЧШИХ ПРОФИТОВ!</b> ✨"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Подтвердить", callback_data=f"profit_confirm_{target_user_id}"),
                    InlineKeyboardButton("🔄 Переделать", callback_data=f"profit_redo_{target_user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat.id,
                photo=image_url,
                caption=caption,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"Ошибка перегенерации изображения: {e}")
            await query.edit_message_caption(
                caption=f"❌ <b>ОШИБКА</b>\n\nНе удалось сгенерировать изображение:\n{str(e)}",
                parse_mode='HTML'
            )

# --- ОТСЛЕЖИВАНИЕ АКТИВНОСТИ ---
async def track_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживает активность пользователей для /ping"""
    if update.message and update.message.from_user:
        update_user_info(update.message.from_user)
    
    # Сохраняем chat_id для периодической рассылки
    if update.message and update.effective_chat:
        chat_id = update.effective_chat.id
        if "broadcast_chats" not in bot_data:
            bot_data["broadcast_chats"] = []
        if chat_id not in bot_data["broadcast_chats"]:
            bot_data["broadcast_chats"].append(chat_id)
            save_data()

# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    """Запуск бота"""
    print("🤖 Запуск DECEPTION TEAM Moderation Bot...")
    print("━━━━━━━━━━━━━━━━━━")
    print(f"📌 Токен бота: {BOT_TOKEN[:20]}...")
    print(f"👮 ID администраторов: {ADMIN_IDS}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды модерации
    print("📝 Регистрация команд модерации...")
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("kicku", kicku_command))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("unwarn", unwarn_command))
    app.add_handler(CommandHandler("warns", warns_command))
    
    # Команды статистики
    print("📊 Регистрация команд статистики...")
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("topd", top_command))
    app.add_handler(CommandHandler("topm", top_command))
    app.add_handler(CommandHandler("mp", mp_command))
    
    # Дополнительные команды
    print("📚 Регистрация дополнительных команд...")
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("manuals", manuals_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("card", card_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("profit", profit_command))
    
    # Обработка callback'ов от кнопок
    app.add_handler(CallbackQueryHandler(handle_profit_callback, pattern="^profit_"))
    
    # Обработка ввода данных для /profit (должен быть перед track_user_activity)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_profit_input), group=0)
    
    # Обработка загруженных изображений для /profit
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_profit_photo), group=0)
    
    # Отслеживание активности пользователей
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_user_activity), group=1)
    
    # Анти-спам и защита от ссылок (должен быть после track_user_activity)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_spam), group=2)
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, check_spam), group=2)
    
    print("✅ Бот запущен!")
    print("━━━━━━━━━━━━━━━━━━")
    print("📝 Доступные команды:")
    print("   👮 Модерация:")
    print("      /mute - замутить пользователя")
    print("      /unmute - размутить пользователя")
    print("      /ban - забанить пользователя")
    print("      /unban - разбанить пользователя")
    print("      /kick - кикнуть пользователя")
    print("      /kicku - кикнуть списком")
    print("      /warn - выдать предупреждение")
    print("      /unwarn - снять предупреждение")
    print("      /warns - показать предупреждения")
    print("   📊 Статистика:")
    print("      /top, /topd, /topm - топ воркеров")
    print("      /mp - личный кабинет")
    print("   📚 Информация:")
    print("      /ping - упомянуть всех пользователей")
    print("      /manuals - мануалы для работы")
    print("      /info - доступные команды")
    print("      /card - реквизиты для оплат (с автоудалением)")
    print("      /card [номер] [банк] - показать карту (с автоудалением)")
    print("      /myid - показать свой ID и статус админа")
    print("   💼 Профиты (только ЛС, только админы):")
    print("      /profit - создать пост о профите")
    print("━━━━━━━━━━━━━━━━━━")
    print("")
    
    app.run_polling()

if __name__ == "__main__":
    main()
