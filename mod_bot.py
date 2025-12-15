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
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8333850560:AAFAP3TGp_2GAraqksxX2KilcTbQCjIIBCE"
ADMIN_IDS = [8495992108]

# Файл для хранения данных
DATA_FILE = "bot_data.json"
# Значения по умолчанию для карты (если еще не заданы в файле)
DEFAULT_CARD_NUMBER = "4400 0000 0000 0000"
DEFAULT_CARD_BANK = "Банк не задан"

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
    
    if ADMIN_IDS and user_id in ADMIN_IDS:
        return True
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
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
    """Обнаруживает все типы ссылок в тексте"""
    patterns = [
        r'https?://[^\s]+',  # HTTP/HTTPS ссылки
        r'www\.[^\s]+',  # WWW ссылки
        r't\.me/[^\s]+',  # Telegram ссылки
        r'@\w+',  # Упоминания (могут быть ссылками)
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
        # Проверяем что есть хотя бы точка или слэш
        if '.' in link or '/' in link or '@' in link or 't.me' in link.lower():
            filtered.append(link)
    
    return list(set(filtered))  # Убираем дубликаты

async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Улучшенная проверка сообщений на спам и ссылки"""
    message = update.message
    
    if not message:
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
    if not await check_command_spam(update, context, "mp", cooldown_seconds=5):
        return
    
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
    if not await check_command_spam(update, context, "info", cooldown_seconds=5):
        return
    
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
            "• /card [номер] [банк] - показать карту (с автоудалением)\n\n"
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
    # Антиспам
    if not await check_command_spam(update, context, "card", cooldown_seconds=5):
        return

    user_is_admin = await is_admin(update, context)

    updated = False

    # Если админ передал аргументы — обновляем карту и сразу показываем список
    if user_is_admin and context.args:
        # Первый аргумент — номер карты, остальные — название банка (может быть с пробелами)
        raw_number = context.args[0]
        bank_name = " ".join(context.args[1:]).strip() or bot_data.get("card_bank", DEFAULT_CARD_BANK)

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
        # Удаляем команду админа, чтобы не светить реквизиты в чате
        try:
            await update.message.delete()
        except:
            pass

    # Показать текущую карту всем (без аргументов или после обновления)
    card_number = bot_data.get("card_number", DEFAULT_CARD_NUMBER)
    bank_name = bot_data.get("card_bank", DEFAULT_CARD_BANK)
    safe_card = html.escape(card_number)
    safe_bank = html.escape(bank_name)

    message_text = (
        f"{'✅ Реквизиты обновлены\n\n' if updated else ''}"
        "💳 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 Для прямых переводов: <b>80%</b>\n"
        "🤝 Через ТП: <b>70%</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Банк: <b>{safe_bank}</b>\n"
        f"💳 Карта: <code>{safe_card}</code>\n\n"
        "⏱ <i>Удаление через: 60 сек</i>"
    )

    try:
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message_text,
            parse_mode='HTML'
        )

        # Обратный отсчет и автоудаление
        async def card_countdown():
            for remaining in range(59, 0, -1):
                await asyncio.sleep(1)
                updated_text = (
                    f"{'✅ Реквизиты обновлены\n\n' if updated else ''}"
                    "💳 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "💰 Для прямых переводов: <b>80%</b>\n"
                    "🤝 Через ТП: <b>70%</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"🏦 Банк: <b>{safe_bank}</b>\n"
                    f"💳 Карта: <code>{safe_card}</code>\n\n"
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
                await sent_message.delete()
            except Exception:
                pass

        asyncio.create_task(card_countdown())

    except Exception as e:
        error_text = f"❌ <b>ОШИБКА</b>\n\nНе удалось отправить сообщение:\n{str(e)}"
        await send_auto_delete_message(context, update.effective_chat.id, error_text, countdown=5)

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
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды модерации
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
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("topd", top_command))
    app.add_handler(CommandHandler("topm", top_command))
    app.add_handler(CommandHandler("mp", mp_command))
    
    # Дополнительные команды
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("manuals", manuals_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("card", card_command))
    
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
    print("━━━━━━━━━━━━━━━━━━")
    print("")
    
    app.run_polling()

if __name__ == "__main__":
    main()
