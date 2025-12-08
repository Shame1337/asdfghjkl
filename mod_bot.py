#!/usr/bin/env python3
"""
DECEPTION TEAM Moderation Bot
Бот для модерации группы с командами администрирования и статистикой
"""
import asyncio
import re
import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8333850560:AAFAP3TGp_2GAraqksxX2KilcTbQCjIIBCE"
ADMIN_IDS = [8495992108]

# Файл для хранения данных
DATA_FILE = "bot_data.json"

# Загрузка/сохранение данных
def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
    return {
        "warnings": {},
        "workers": {},
        "users": {},
        "users": {},
        "command_cooldowns": {},  # user_id: {command: timestamp}
        "last_bot_messages": {}   # user_id: {chat_id: int, message_id: int}
    }

def save_data():
    """Сохранение данных в файл"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(bot_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")

# Глобальные данные
bot_data = load_data()


def update_user_info(user):
    """Обновляет информацию о пользователе"""
    user_id = str(user.id)
    bot_data["users"][user_id] = {
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "last_seen": datetime.now().isoformat()
    }
    save_data()


# --- АНТИСПАМ ДЛЯ КОМАНД ---
# --- АНТИСПАМ ДЛЯ КОМАНД ---
async def check_command_spam(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str, cooldown_seconds: int = 5) -> bool:
    """
    Проверяет можно ли использовать команду (антиспам)
    Возвращает True если можно использовать, False если нужно подождать
    """
    user_id = str(update.effective_user.id)
    current_time = datetime.now().timestamp()
    
    # Инициализируем структуру если её нет
    if "command_cooldowns" not in bot_data:
        bot_data["command_cooldowns"] = {}
    
    if user_id not in bot_data["command_cooldowns"]:
        bot_data["command_cooldowns"][user_id] = {}
        
    # Инициализируем счетчик спама
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
                # Сбрасываем счетчик
                bot_data["spam_counts"][user_id]["count"] = 0
                
                # Выдаем варн
                if "warns" not in bot_data:
                    bot_data["warns"] = {}
                if user_id not in bot_data["warns"]:
                    bot_data["warns"][user_id] = []
                
                bot_data["warns"][user_id].append({
                    "reason": "Спам командами",
                    "date": datetime.now().isoformat()
                })
                save_data()
                
                warn_count = len(bot_data["warns"][user_id])
                
                message_text = (
                    f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
                    f"👤 Пользователь: {update.effective_user.mention_html()}\n"
                    f"📝 Причина: Спам командами\n"
                    f"🔢 Предупреждений: {warn_count}/3"
                )
                await send_auto_delete_message(context, update.effective_chat.id, message_text)
                
                # Проверка на бан
                if warn_count >= 3:
                    try:
                        await context.bot.ban_chat_member(update.effective_chat.id, int(user_id))
                        ban_text = f"🔨 {update.effective_user.mention_html()} забанен за 3 предупреждения!"
                        await send_auto_delete_message(context, update.effective_chat.id, ban_text)
                    except:
                        pass
            
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
    # Это обеспечивает "Single Active Message"
    if "last_bot_messages" in bot_data and user_id in bot_data["last_bot_messages"]:
        last_msg = bot_data["last_bot_messages"][user_id]
        try:
            await context.bot.delete_message(chat_id=last_msg['chat_id'], message_id=last_msg['message_id'])
        except:
            pass
        # Удаляем запись
        del bot_data["last_bot_messages"][user_id]
        save_data()

    # Обновляем время последнего использования
    bot_data["command_cooldowns"][user_id][command_name] = current_time
    save_data()
    return True


# --- АВТОУДАЛЕНИЕ СООБЩЕНИЙ ---
async def send_auto_delete_message(context, chat_id, text, parse_mode='HTML', countdown=10):
    """Отправляет сообщение с обратным отсчетом и автоудалением (в фоне)"""
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=f"{text}\n\n⏱ Удаление через: {countdown} сек",
        parse_mode=parse_mode
    )
    
    async def delete_process():
        for i in range(countdown - 1, 0, -1):
            await asyncio.sleep(1)
            try:
                await message.edit_text(
                    f"{text}\n\n⏱ Удаление через: {i} сек",
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
    
    time_str = time_str.lower()
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    
    try:
        if time_str[-1] in multipliers:
            return int(time_str[:-1]) * multipliers[time_str[-1]]
        return int(time_str)
    except:
        return 0


# --- КОМАНДЫ МОДЕРАЦИИ ---
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mute"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
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
        
        message_text = (
            f"🔇 <b>МЬЮТ</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"⏱ Время: {time_str}\n"
            f"📝 Причина: {reason}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except:
        pass


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ban"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    
    # Проверяем что не пытаемся забанить бота
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
        
        message_text = (
            f"🔨 <b>БАН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"⏱ Время: {time_str}\n"
            f"📝 Причина: {reason}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except Exception as e:
        print(f"Ошибка бана: {e}")


async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /kick"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "Нарушение правил"
    
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        
        message_text = (
            f"👢 <b>КИК</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"📝 Причина: {reason}"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except:
        pass


async def kicku_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /kicku - кикнуть пользователей по юзернейму"""
    if not await is_admin(update, context):
        return

    if not context.args:
        await send_auto_delete_message(context, update.effective_chat.id, "⚠️ Укажите юзернеймы через пробел: /kicku @user1 @user2")
        return

    # 1. Собираем ID из найденных меншнов (если пользователь выбирал из подсказок)
    ids_to_kick = set()
    targets = {}  # user_id/username -> status
    
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'text_mention' and entity.user:
                ids_to_kick.add(entity.user.id)
                targets[f"@{entity.user.username or entity.user.first_name}"] = {"id": entity.user.id, "resolved": True}

    # Создаем карту username -> user_id из БД для поиска
    username_to_id = {}
    if "users" in bot_data:
        for uid, info in bot_data["users"].items():
            if info.get("username"):
                username_to_id[info["username"].lower()] = uid

    # 2. Проходимся по аргументам
    for arg in context.args:
        clean_arg = arg.lstrip('@').strip(',')
        lower_arg = clean_arg.lower()
        
        # Если это уже найденный через text_mention ID - пропускаем
        # (сложно сопоставить аргумент с сущностью, поэтому просто идем дальше, если ID уже есть в ids_to_kick это ок)
        
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
                # Пауза перед запросом чтобы не словить лимит
                await asyncio.sleep(0.2) 
                
                # get_chat требует @ для юзернеймов
                search_query = f"@{clean_arg}"
                chat_obj = await context.bot.get_chat(search_query)
                user_id = chat_obj.id
            except Exception as e:
                error_reason = str(e)

        if user_id:
            ids_to_kick.add(user_id)
            targets[arg] = {"id": user_id, "resolved": True}
        else:
             # Если не нашли ID но еще не записали ошибку
            if arg not in targets:
                targets[arg] = {"resolved": False, "error": error_reason or "Не удалось определить ID"}

    # 3. Выполняем кик
    kicked_users = []
    errors = []

    for uid in ids_to_kick:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, uid)
            await context.bot.unban_chat_member(update.effective_chat.id, uid)
            
            # Пытаемся найти имя для отчета
            name = str(uid)
            # Ищем в targets
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
    message_text = "👢 <b>МАССОВЫЙ КИК</b>\n\n"
    
    if kicked_users:
        message_text += f"✅ <b>Кикнуты ({len(kicked_users)}):</b>\n" + ", ".join(kicked_users) + "\n\n"
        
    if errors:
        # Ограничиваем длину
        error_msg = "\n".join(errors)
        if len(error_msg) > 1500:
            error_msg = error_msg[:1500] + "\n...и другие"
        message_text += f"❌ <b>Ошибки ({len(errors)}):</b>\n" + error_msg

    await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=10)


async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /warn"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "Нарушение правил"
    
    user_id = str(user.id)
    if user_id not in bot_data["warns"]:
        bot_data["warns"][user_id] = []
    
    bot_data["warns"][user_id].append({
        "reason": reason,
        "date": datetime.now().isoformat()
    })
    save_data()
    
    warn_count = len(bot_data["warns"][user_id])
    
    message_text = (
        f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
        f"👤 Пользователь: {user.mention_html()}\n"
        f"📝 Причина: {reason}\n"
        f"🔢 Предупреждений: {warn_count}/3"
    )
    await send_auto_delete_message(context, update.effective_chat.id, message_text)
    
    if warn_count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            ban_text = f"🔨 {user.mention_html()} забанен за 3 предупреждения!"
            await send_auto_delete_message(context, update.effective_chat.id, ban_text)
        except:
            pass


# --- КОМАНДЫ ОТМЕНЫ ---
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unmute - снять мут"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    
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
            f"🔊 <b>РАЗМУТ</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"✅ Мут снят"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except:
        pass


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unban - разбанить"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    
    try:
        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user.id,
            only_if_banned=True
        )
        
        message_text = (
            f"✅ <b>РАЗБАН</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"✅ Бан снят"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    except:
        pass


async def unwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /unwarn - снять предупреждение"""
    if not await is_admin(update, context):
        return
    
    if not update.message.reply_to_message:
        return
    
    user = update.message.reply_to_message.from_user
    user_id = str(user.id)
    
    if user_id in bot_data["warns"] and bot_data["warns"][user_id]:
        bot_data["warns"][user_id].pop()  # Удаляем последнее предупреждение
        save_data(bot_data)
        
        warn_count = len(bot_data["warns"][user_id])
        
        message_text = (
            f"✅ <b>СНЯТО ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"🔢 Предупреждений осталось: {warn_count}/3"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)
    else:
        message_text = (
            f"ℹ️ <b>ИНФОРМАЦИЯ</b>\n\n"
            f"👤 Пользователь: {user.mention_html()}\n"
            f"У пользователя нет предупреждений"
        )
        await send_auto_delete_message(context, update.effective_chat.id, message_text)


# --- АНТИ-СПАМ ---
async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет сообщения на спам и ссылки"""
    message = update.message
    
    if not message or not message.text:
        return
    
    if await is_admin(update, context):
        return
    
    text = message.text.lower()
    telegram_links = re.findall(r'(t\.me/|@\w+|https?://t\.me)', text)
    
    if telegram_links:
        try:
            await message.delete()
            
            user_id = str(message.from_user.id)
            if user_id not in bot_data["warns"]:
                bot_data["warns"][user_id] = []
            
            bot_data["warns"][user_id].append({
                "reason": "Отправка ссылок",
                "date": datetime.now().isoformat()
            })
            save_data(bot_data)
            
            warn_count = len(bot_data["warns"][user_id])
            
            warning_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ {message.from_user.mention_html()}\n"
                     f"Запрещено отправлять ссылки!\n"
                     f"Предупреждений: {warn_count}/3",
                parse_mode='HTML'
            )
            
            await asyncio.sleep(5)
            await warning_msg.delete()
        except:
            pass


# --- СТАТИСТИКА ---
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /top"""
    # Проверка антиспама
    if not await check_command_spam(update, context, "top", cooldown_seconds=5):
        return
    
    command = update.message.text.split()[0][1:]
    period = "месяц" if command == "topm" else "день"
    
    message = f"""📊 <b>ТОП ВОРКЕРОВ ЗА {period.upper()}</b>

⚠️ <i>Функция в разработке</i>

Здесь будет отображаться:
• Топ воркеров по профитам
• Количество профитов
• Общая сумма

Скоро будет доступна полная статистика!"""
    
    sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message)
    if sent_msg:
        if "last_bot_messages" not in bot_data: bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_msg.chat.id,
            'message_id': sent_msg.message_id
        }
        save_data()


async def mp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mp"""
    # Проверка антиспама
    if not await check_command_spam(update, context, "mp", cooldown_seconds=5):
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in bot_data["workers"]:
        bot_data["workers"][user_id] = {
            "tag": user.username or "Аноним",
            "profits_day": 0,
            "profits_month": 0,
            "total": 0
        }
        save_data(bot_data)
    
    worker = bot_data["workers"][user_id]
    
    message = f"""👤 <b>ЛИЧНЫЙ КАБИНЕТ ВОРКЕРА</b>

🏷 <b>Тег:</b> @{worker['tag']}
📊 <b>Статус:</b> Воркер

⚠️ <i>Функция в разработке</i>

Здесь будет отображаться:
• Статистика за день/месяц
• Общее количество профитов
• Среднее количество профитов

Скоро будет доступна полная статистика!"""
    
    sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message)
    if sent_msg:
        if "last_bot_messages" not in bot_data: bot_data["last_bot_messages"] = {}
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
    
    # Проверка антиспама (10 секунд для ping)
    if not await check_command_spam(update, context, "ping", cooldown_seconds=10):
        return
    
    # Получаем всех участников чата
    try:
        chat_id = update.effective_chat.id
        
        # Проверяем наличие ключа users
        if "users" not in bot_data:
            bot_data["users"] = {}
            save_data()
        
        # Собираем всех пользователей из базы
        mentions = []
        for user_id, user_info in bot_data["users"].items():
            if user_info.get("username"):
                mentions.append(f"@{user_info['username']}")
            else:
                # Используем mention по ID если нет username
                mentions.append(f"<a href='tg://user?id={user_id}'>{user_info.get('first_name', 'User')}</a>")
        
        if not mentions:
            message_text = "ℹ️ <b>Нет сохраненных пользователей</b>\n\nПользователи появятся после их активности в чате"
            await send_auto_delete_message(context, update.effective_chat.id, message_text)
            return
        
        # Разбиваем на группы по 5 пользователей для читаемости
        chunk_size = 5
        mention_chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
        
        message_text = f"📢 <b>PING ВСЕХ УЧАСТНИКОВ</b>\n\n"
        for chunk in mention_chunks:
            message_text += " ".join(chunk) + "\n"
        
        message_text += f"\n👥 Всего: {len(mentions)} пользователей"
        
        sent_msg = await send_auto_delete_message(context, update.effective_chat.id, message_text, countdown=15)
        if sent_msg:
            if "last_bot_messages" not in bot_data: bot_data["last_bot_messages"] = {}
            bot_data["last_bot_messages"][str(update.effective_user.id)] = {
                'chat_id': sent_msg.chat.id,
                'message_id': sent_msg.message_id
            }
            save_data()
    except Exception as e:
        print(f"Ошибка в ping_command: {e}")


async def manuals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /manuals - отправляет ссылку на мануалы"""
    # Проверка антиспама
    if not await check_command_spam(update, context, "manuals", cooldown_seconds=5):
        return
    
    try:
        # Создаем inline кнопку
        keyboard = [
            [InlineKeyboardButton("📖 Читать мануалы", url="https://telegra.ph/Manula-po-NARKO--DecepTeam-12-05")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            "📚 <b>МАНУАЛЫ ДЛЯ РАБОТЫ</b>\n\n"
            "Для прочтения мануалов по работе нажмите на кнопку ниже 👇\n\n"
            "⏱ Удаление через: 10 сек"
        )
        
        # Отправляем сообщение как reply на сообщение пользователя
        sent_message = await update.message.reply_text(
            text=message_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        # Сохраняем сообщение для Single Active Message
        if "last_bot_messages" not in bot_data: bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_message.chat.id,
            'message_id': sent_message.message_id
        }
        save_data()

        async def manuals_countdown():
            # Обратный отсчет и удаление
            for remaining in range(9, 0, -1):
                await asyncio.sleep(1)
                updated_text = (
                    "📚 <b>МАНУАЛЫ ДЛЯ РАБОТЫ</b>\n\n"
                    "Для прочтения мануалов по работе нажмите на кнопку ниже 👇\n\n"
                    f"⏱ Удаление через: {remaining} сек"
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
    """Команда /info - показывает доступные команды для воркеров"""
    # Проверка антиспама
    if not await check_command_spam(update, context, "info", cooldown_seconds=5):
        return
    
    try:
        message_text = (
            "ℹ️ <b>ДОСТУПНЫЕ КОМАНДЫ</b>\n\n"
            "📋 <b>Основные команды:</b>\n"
            "/info - показать это сообщение\n"
            "/manuals - мануалы для работы\n"
            "📊 <b>Статистика:</b>\n"
            "/top - топ воркеров (общий)\n"
            "/topd - топ воркеров (за день)\n"
            "/topm - топ воркеров (за месяц)\n"
            "/mp - личный кабинет\n\n"
            "⏱ Удаление через: 5:00"
        )
        
        sent_message = await update.message.reply_text(
            text=message_text,
            parse_mode='HTML'
        )
        
        # Сохраняем сообщение для Single Active Message
        if "last_bot_messages" not in bot_data: bot_data["last_bot_messages"] = {}
        bot_data["last_bot_messages"][str(update.effective_user.id)] = {
            'chat_id': sent_message.chat.id,
            'message_id': sent_message.message_id
        }
        save_data()

        async def info_countdown():
            # Обратный отсчет 5 минут (300 секунд)
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
                    "📋 <b>Основные команды:</b>\n"
                    "/info - показать это сообщение\n"
                    "/manuals - мануалы для работы\n"
                    "📊 <b>Статистика:</b>\n"
                    "/top - топ воркеров (общий)\n"
                    "/topd - топ воркеров (за день)\n"
                    "/topm - топ воркеров (за месяц)\n"
                    "/mp - личный кабинет\n\n"
                    f"⏱ Удаление через: {time_str}"
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





# --- ОТСЛЕЖИВАНИЕ АКТИВНОСТИ ---
async def track_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживает активность пользователей для /ping"""
    if update.message and update.message.from_user:
        update_user_info(update.message.from_user)


# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    """Запуск бота"""
    print("🤖 Запуск DECEPTION TEAM Moderation Bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("kicku", kicku_command))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("unwarn", unwarn_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("topd", top_command))
    app.add_handler(CommandHandler("topm", top_command))
    app.add_handler(CommandHandler("mp", mp_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("manuals", manuals_command))
    app.add_handler(CommandHandler("info", info_command))
    
    # Отслеживание активности пользователей
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_user_activity), group=1)
    
    # Анти-спам (должен быть после track_user_activity)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_spam), group=2)
    
    print("✅ Бот запущен!")
    print("📝 Доступные команды:")
    print("   /mute - замутить пользователя")
    print("   /unmute - размутить пользователя")
    print("   /ban - забанить пользователя")
    print("   /unban - разбанить пользователя")
    print("   /kick - кикнуть пользователя")
    print("   /kicku - кикнуть списком (@user1 @user2)")
    print("   /warn - выдать предупреждение")
    print("   /unwarn - снять предупреждение")
    print("   /ping - упомянуть всех пользователей")
    print("   /manuals - мануалы для работы")
    print("   /info - доступные команды")
    print("   /top, /topd, /topm - топ воркеров")
    print("   /mp - личный кабинет")
    print("")
    
    app.run_polling()


if __name__ == "__main__":
    main()
