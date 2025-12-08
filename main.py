import asyncio
import logging
import sys
import json
import re
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter, BaseFilter
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# TOKEN
TOKEN = "8586422657:AAEQYDfdW718B3WjCtlCT7Tkyhe2QCZQ1LI"

# CHANNEL ID
CHANNEL_ID = -1003366532574

# ADMIN ID
ADMIN_ID = 8495992108

DATA_FILE = "data.json"

dp = Dispatcher(storage=MemoryStorage())

# User States
PENDING = "PENDING"
ACCEPTED = "ACCEPTED"

# User Actions
WAITING_RECEIPT = "WAITING_RECEIPT"

# --- JSON PERSISTENCE HELPERS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}, []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        users = data.get("users", {})
        curators_list = data.get("curators", [])
        for uid, udata in users.items():
            if "join_time" in udata and udata["join_time"]:
                try:
                    udata["join_time"] = datetime.fromisoformat(udata["join_time"])
                except ValueError:
                    udata["join_time"] = None
        users_int_keys = {int(k): v for k, v in users.items()}
        return users_int_keys, curators_list
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return {}, []

def save_data():
    try:
        users_serializable = {}
        for uid, udata in user_data.items():
            u_copy = udata.copy()
            if "join_time" in u_copy and isinstance(u_copy["join_time"], datetime):
                u_copy["join_time"] = u_copy["join_time"].isoformat()
            users_serializable[str(uid)] = u_copy
        data = {
            "users": users_serializable,
            "curators": curators
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Failed to save data: {e}")

# Load data
user_data, curators = load_data()

# Admin FSM States
class AddCurator(StatesGroup):
    waiting_for_id = State()
    waiting_for_nick = State()
    waiting_for_about = State()
    waiting_for_exp = State()
    waiting_for_percent = State()

# Application FSM
class ApplicationState(StatesGroup):
    waiting_for_reason = State()
    curator_id = State() # Store target curator ID here

# Settings FSM States
class SettingsState(StatesGroup):
    waiting_for_tag = State()
    waiting_for_about = State()

# --- Keyboards ---
def get_main_menu_keyboard(manuals_link=None):
    # If manuals_link is provided, replace the "Manuals" button with the Link button
    # UPDATE: User requested static Telegra.ph link
    manuals_btn = InlineKeyboardButton(text="📚 Мануал", url="https://telegra.ph/Manula-po-NARKO--DecepTeam-12-05")

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Проверка чека", callback_data="menu_check_receipt")],
        [InlineKeyboardButton(text="💬 Чат воркеров", callback_data="menu_chat"),
         InlineKeyboardButton(text="👥 Кураторы", callback_data="menu_curators")],
        [InlineKeyboardButton(text="🏆 Топ воркеров", callback_data="menu_top"),
         manuals_btn],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton(text="🤖 Ворк бот", callback_data="menu_work_bot")]
    ])

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])

# ... (Previous code remains) ...

@dp.callback_query(F.data.startswith("apply_curator_"))
async def apply_curator_callback(callback: CallbackQuery, state: FSMContext):
    curator_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Check if already applied
    user_info = user_data.get(user_id, {})
    user_apps = user_info.get("applications", [])
    
    if curator_id in user_apps:
        await callback.answer("❌ Вы уже подали заявку этому куратору.", show_alert=True)
        return

    # Start application flow
    await state.update_data(target_curator_id=curator_id)
    await state.set_state(ApplicationState.waiting_for_reason)
    
    await callback.message.edit_text("✍️ <b>Почему вы хотите к данному куратору в ученики?</b>\nНапишите краткий ответ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="menu_curators")]]))
    await callback.answer()

@dp.message(ApplicationState.waiting_for_reason)
async def process_application_reason(message: Message, state: FSMContext):
    reason = message.text
    data = await state.get_data()
    target_curator_id = data.get("target_curator_id")
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Save application to prevent duplicates
    if user_id not in user_data:
        user_data[user_id] = {}
        
    if "applications" not in user_data[user_id]:
        user_data[user_id]["applications"] = []
        
    user_data[user_id]["applications"].append(target_curator_id)
    save_data()
    
    # Notify Curator with Buttons
    try:
        msg_text = (
            f"🔔 <b>Новая заявка!</b>\n"
            f"👤 Пользователь: @{username} (ID: <code>{user_id}</code>)\n"
            f"📝 <b>Причина:</b> {reason}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"curator_decide_accept_{user_id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"curator_decide_reject_{user_id}")]
        ])
        
        await message.bot.send_message(chat_id=target_curator_id, text=msg_text, reply_markup=keyboard)
        await message.answer("✅ Ваша заявка отправлена куратору! Ожидайте решения.", reply_markup=get_back_button())
    except Exception as e:
        await message.answer("❌ Не удалось отправить заявку. Возможно, куратор недоступен.", reply_markup=get_back_button())
        logging.error(f"Failed to notify curator: {e}")
        
    await state.clear()

@dp.callback_query(F.data.startswith("curator_decide_"))
async def curator_decision_callback(callback: CallbackQuery):
    # Data format: curator_decide_ACTION_USERID
    parts = callback.data.split("_")
    action = parts[2] # accept / reject
    target_user_id = int(parts[3])
    
    curator_nick = "Куратор" # We could lookup nick if needed
    
    if action == "accept":
        await callback.bot.send_message(chat_id=target_user_id, text=f"🎉 <b>Поздравляем!</b> {curator_nick} принял вашу заявку!")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n✅ <b>Заявка принята.</b>")
    elif action == "reject":
        await callback.bot.send_message(chat_id=target_user_id, text=f"😔 {curator_nick} отклонил вашу заявку.")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n❌ <b>Заявка отклонена.</b>")
    
    await callback.answer()
    # If manuals_link is provided, replace the "Manuals" button with the Link button
    if manuals_link:
        manuals_btn = InlineKeyboardButton(text="🔗 Вступить (5 мин)", url=manuals_link)
    else:
        manuals_btn = InlineKeyboardButton(text="📚 Мануалы", callback_data="menu_manuals")

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Проверка чека", callback_data="menu_check_receipt")],
        [InlineKeyboardButton(text="💬 Чат воркеров", callback_data="menu_chat"),
         InlineKeyboardButton(text="👥 Кураторы", callback_data="menu_curators")],
        [InlineKeyboardButton(text="🏆 Топ воркеров", callback_data="menu_top"),
         manuals_btn],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")]
    ])

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])

# --- HELPERS ---
def get_profile_text(user_id):
    user_info = user_data.get(user_id, {})
    join_time = user_info.get("join_time")
    
    if join_time:
        duration = datetime.now() - join_time
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{days} дней {hours} часов {minutes} минут {seconds} секунд"
    else:
        time_str = "0 секунд"
    
    about = user_info.get("about", "Не указано")
    custom_tag = user_info.get("tag", "")
    tag_display = f"[{custom_tag}]" if custom_tag else ""
    
    # Mentor Logic
    mentor_text = ""
    mentor_id = user_info.get("mentor_id")
    if mentor_id:
        mentor = next((c for c in curators if c['id'] == mentor_id), None)
        if mentor:
            mentor_text = f"\n👤 Наставник:\n┖ {mentor['nick']}\n"
    
    return (
        f"👤 Ваш профиль: <code>{user_id}</code> {tag_display}\n"
        f"┖ 🛡 Статус: <b>Воркер</b>\n\n"
        f"📊 Статистика:\n"
        f"┖ 💰 Профиты: отсутствуют\n\n"
        f"📝 О себе:\n"
        f"┖ {about}\n\n"
        f"⏳ С нами:\n"
        f"┖ {time_str}\n"
        f"{mentor_text}"
    )

# ... (Start Handler and other callbacks) ...

@dp.callback_query(F.data.startswith("curator_decide_"))
async def curator_decision_callback(callback: CallbackQuery):
    # Data format: curator_decide_ACTION_USERID
    parts = callback.data.split("_")
    action = parts[2] # accept / reject
    target_user_id = int(parts[3])
    curator_id = callback.from_user.id
    
    curator = next((c for c in curators if c['id'] == curator_id), None)
    curator_nick = curator['nick'] if curator else "Куратор"
    
    if action == "accept":
        # Save mentor assignment
        if target_user_id not in user_data:
            user_data[target_user_id] = {}
        
        user_data[target_user_id]["mentor_id"] = curator_id
        save_data()
        
        await callback.bot.send_message(chat_id=target_user_id, text=f"🎉 <b>Поздравляем!</b> {curator_nick} принял вашу заявку!")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n✅ <b>Заявка принята.</b>")
    elif action == "reject":
        await callback.bot.send_message(chat_id=target_user_id, text=f"😔 {curator_nick} отклонил вашу заявку.")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n❌ <b>Заявка отклонена.</b>")
    
    await callback.answer()
@dp.message(CommandStart())
async def command_start_handler(message: Message):
    user_id = message.from_user.id
    user_info = user_data.get(user_id, {})
    current_state = user_info.get("state")
    
    if current_state == ACCEPTED:
        # Show Profile text instead of "Main Menu"
        text = get_profile_text(user_id)
        await message.answer(text, reply_markup=get_main_menu_keyboard())
        return

    if current_state == PENDING:
        await message.answer("🕒 Вы уже подали заявку, ожидайте решения.")
        return

    # New User Flow
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Согласен", callback_data="agree")]
    ])
    
    text = (
        "👋 Добро пожаловать в наш <b>MAIN BOT</b>!\n\n"
        "Для вступления в нашу тииму необходимо подать заявку.\n\n"
        "📜 Вы согласны с условиями?"
    )
    
    await message.answer(text, reply_markup=keyboard)

# --- Initial Flow Callbacks ---
@dp.callback_query(F.data == "agree")
async def agree_callback(callback: CallbackQuery):
    await callback.message.delete()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="has_exp_yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="has_exp_no")]
    ])
    text = "❓ Есть ли у вас опыт в данной сфере?"
    await callback.answer() 
    await callback.message.answer(text, reply_markup=keyboard)

@dp.callback_query(F.data.in_({"has_exp_yes", "has_exp_no"}))
async def experience_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()
    
    text = "🚀 Отлично, ваша заявка успешно подана! Ожидайте сообщения от бота."
    await callback.message.answer(text)
    await callback.answer()
    
    if user_id not in user_data:
        user_data[user_id] = {}
        
    user_data[user_id]["state"] = PENDING
    save_data()
    
    await asyncio.sleep(10)
    
    user_data[user_id]["state"] = ACCEPTED
    user_data[user_id]["join_time"] = datetime.now()
    save_data()
    
    final_text = (
        "🎉 <b>Поздравляем!</b>\n"
        "Вы приняты в тиму <b>Deception Team</b>.\n"
        "Для работы с MAIN ботом напишите /start"
    )
    await callback.bot.send_message(chat_id=user_id, text=final_text)

# --- BACK TO MENU CALLBACK ---
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    # Show Profile text instead of "Main Menu"
    text = get_profile_text(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- PROFILE CALLBACK ---
@dp.callback_query(F.data == "menu_profile")
async def profile_callback(callback: CallbackQuery):
    # Just refresh the profile view (it's the same as main menu now)
    text = get_profile_text(callback.from_user.id)
    # We use edit_text with main menu keyboard because profile IS the main view now
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await callback.answer("🔄 Профиль обновлен")

# --- RECEIPT CHECK CALLBACK ---
@dp.callback_query(F.data == "menu_check_receipt")
async def check_receipt_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data[user_id]["action"] = WAITING_RECEIPT
    save_data()
    
    text = (
        "💸 <b>Проверка чека</b>\n"
        "📸 Отправьте сюда чек для проверки.\n\n"
        "⚠️ <b>Правила:</b>\n"
        "❗️ Отправка изображений, не относящихся к чекам, приведет к блокировке кнопки."
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()

@dp.message(F.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id
    user_info = user_data.get(user_id, {})
    
    if user_info.get("action") == WAITING_RECEIPT:
        try:
            await message.forward(chat_id=CHANNEL_ID)
            # Send success message with Back button (since we can't edit the photo message)
            await message.answer("✅ Ваш чек отправлен на проверку!", reply_markup=get_back_button())
            user_data[user_id]["action"] = None
            save_data()
        except Exception as e:
            logging.error(f"Failed to forward message: {e}")
            await message.answer("❌ Ошибка при отправке. Проверьте ID канала (в коде) и права бота.")

# --- CURATORS CALLBACK ---
@dp.callback_query(F.data == "menu_curators")
async def curators_callback(callback: CallbackQuery):
    text = (
        "👥 <b>Кураторы</b>\n"
        "Здесь вы можете выбрать опытного куратора для помощи в работе.\n"
        "Он подскажет стратегии и ответит на ваши вопросы."
    )
    
    buttons = []
    
    # Add Admin features
    if callback.from_user.id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="➕ Добавить куратора", callback_data="admin_add_curator")])
        
    for c in curators:
        buttons.append([InlineKeyboardButton(text=f"👤 {c['nick']}", callback_data=f"view_curator_{c['id']}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")])
        
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("view_curator_"))
async def view_curator_callback(callback: CallbackQuery):
    try:
        curator_id = int(callback.data.split("_")[2])
        curator = next((c for c in curators if c['id'] == curator_id), None)
        
        if not curator:
            await callback.answer("❌ Куратор не найден.")
            return

        text = (
            f"👤 <b>Ник куратора:</b> {curator['nick']}\n"
            f"ℹ️ <b>О себе:</b> {curator['about']}\n"
            f"🕰 <b>Опыт работы:</b> {curator['exp']}\n"
            f"💵 <b>Процент с 5 профитов:</b> {curator['percent']}\n"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📩 Подать заявку", callback_data=f"apply_curator_{curator_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_curators")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {e}")

# Note: The actual apply logic is now handled by the FSM handlers defined above.
# We need to make sure the OLD simple handler is removed or overwritten.
# The code below REPLACES the old handler with the FSM initiation logic.

@dp.callback_query(F.data.startswith("apply_curator_"))
async def apply_curator_callback(callback: CallbackQuery, state: FSMContext):
    curator_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Check if already applied
    user_info = user_data.get(user_id, {})
    user_apps = user_info.get("applications", [])
    
    if curator_id in user_apps:
        await callback.answer("❌ Вы уже подали заявку этому куратору.", show_alert=True)
        return

    # Start application flow
    await state.update_data(target_curator_id=curator_id)
    await state.set_state(ApplicationState.waiting_for_reason)
    
    await callback.message.edit_text("✍️ <b>Почему вы хотите к данному куратору в ученики?</b>\nНапишите краткий ответ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="menu_curators")]]))
    await callback.answer()

@dp.message(ApplicationState.waiting_for_reason)
async def process_application_reason(message: Message, state: FSMContext):
    reason = message.text
    data = await state.get_data()
    target_curator_id = data.get("target_curator_id")
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Save application to prevent duplicates
    if user_id not in user_data:
        user_data[user_id] = {}
        
    if "applications" not in user_data[user_id]:
        user_data[user_id]["applications"] = []
        
    user_data[user_id]["applications"].append(target_curator_id)
    save_data()
    
    # Notify Curator with Buttons
    try:
        msg_text = (
            f"🔔 <b>Новая заявка!</b>\n"
            f"👤 Пользователь: @{username} (ID: <code>{user_id}</code>)\n"
            f"📝 <b>Причина:</b> {reason}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"curator_decide_accept_{user_id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"curator_decide_reject_{user_id}")]
        ])
        
        await message.bot.send_message(chat_id=target_curator_id, text=msg_text, reply_markup=keyboard)
        await message.answer("✅ Ваша заявка отправлена куратору! Ожидайте решения.", reply_markup=get_back_button())
    except Exception as e:
        await message.answer("❌ Не удалось отправить заявку. Возможно, куратор недоступен.", reply_markup=get_back_button())
        logging.error(f"Failed to notify curator: {e}")
        
    await state.clear()

@dp.callback_query(F.data.startswith("curator_decide_"))
async def curator_decision_callback(callback: CallbackQuery):
    # Data format: curator_decide_ACTION_USERID
    parts = callback.data.split("_")
    action = parts[2] # accept / reject
    target_user_id = int(parts[3])
    
    curator_nick = "Куратор" 
    
    if action == "accept":
        await callback.bot.send_message(chat_id=target_user_id, text=f"🎉 <b>Поздравляем!</b> {curator_nick} принял вашу заявку!")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n✅ <b>Заявка принята.</b>")
    elif action == "reject":
        await callback.bot.send_message(chat_id=target_user_id, text=f"😔 {curator_nick} отклонил вашу заявку.")
        await callback.message.edit_text(f"{callback.message.html_text}\n\n❌ <b>Заявка отклонена.</b>")
    
    await callback.answer()

# --- MANUALS CALLBACK ---
@dp.callback_query(F.data == "menu_manuals")
async def manuals_callback(callback: CallbackQuery):
    try:
        expire_time = datetime.now() + timedelta(minutes=5)
        # Unique name for the link
        link_name = f"Manual_{callback.from_user.id}_{int(expire_time.timestamp())}"
        
        link = await callback.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=expire_time,
            name=link_name
        )
        
        # In-place update: Regenerate main menu but with the link button
        new_keyboard = get_main_menu_keyboard(manuals_link=link.invite_link)
        
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        await callback.answer("✅ Ссылка создана! Жми кнопку.", show_alert=True)
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Failed to create invite link: {error_msg}")
        # Show specific error to user to help debug
        await callback.answer(f"❌ Ошибка: {error_msg}. \nПроверьте права бота и CHANNEL_ID!", show_alert=True)

# --- SETTINGS CALLBACK ---
@dp.callback_query(F.data == "menu_settings")
async def settings_callback(callback: CallbackQuery):
    text = "⚙️ <b>Настройки</b>\nВыберите, что хотите изменить:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Изменить тег", callback_data="settings_change_tag")],
        [InlineKeyboardButton(text="📝 Изменить 'О себе'", callback_data="settings_change_about")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "settings_change_tag")
async def settings_change_tag(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите новый тег (до 7 символов, без ссылок, только буквы/цифры):")
    await state.set_state(SettingsState.waiting_for_tag)
    await callback.answer()

@dp.message(SettingsState.waiting_for_tag)
async def process_new_tag(message: Message, state: FSMContext):
    tag = message.text
    user_id = message.from_user.id
    
    if len(tag) > 7:
        await message.answer("❌ Тег слишком длинный! Максимум 7 символов. Попробуйте снова:")
        return
    
    if re.search(r'http[s]?://|www\.|t\.me', tag):
        await message.answer("❌ Нельзя ставить ссылку, поставь другое значение.")
        return
        
    if not re.match(r'^[a-zA-Zа-яА-Я0-9]+$', tag):
        await message.answer("❌ Тег должен содержать только буквы или цифры. Попробуйте снова:")
        return

    if user_id not in user_data:
        user_data[user_id] = {}
        
    user_data[user_id]["tag"] = tag
    save_data()
    
    await message.answer(f"✅ Тег успешно изменен на: <b>{tag}</b>", reply_markup=get_back_button())
    await state.clear()

@dp.callback_query(F.data == "settings_change_about")
async def settings_change_about(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите информацию о себе:")
    await state.set_state(SettingsState.waiting_for_about)
    await callback.answer()

@dp.message(SettingsState.waiting_for_about)
async def process_new_about(message: Message, state: FSMContext):
    about = message.text
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
        
    user_data[user_id]["about"] = about
    save_data()
    
    await message.answer("✅ Информация 'О себе' обновлена!", reply_markup=get_back_button())
    await state.clear()

# --- Admin Handlers (Add Curator) ---
@dp.callback_query(F.data == "admin_add_curator")
async def admin_add_curator_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен.", show_alert=True)
        return
    
    await callback.message.answer("🆔 Введите ID куратора (число):")
    await state.set_state(AddCurator.waiting_for_id)
    await callback.answer()

@dp.message(Command("add_curator"))
async def cmd_add_curator(message: Message, state: FSMContext):
    # Debug: Print user ID to console
    print(f"DEBUG: /add_curator called by {message.from_user.id}. Expected ADMIN_ID: {ADMIN_ID}")
    
    if message.from_user.id != ADMIN_ID:
        # Debug: Tell user they are not admin
        await message.answer(f"❌ У вас нет прав. Ваш ID: <code>{message.from_user.id}</code>. Требуется: <code>{ADMIN_ID}</code>")
        return

    # Check for arguments
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        # Argument provided: /add_curator 123456
        curator_id = int(args[1])
        await state.update_data(id=curator_id)
        await message.answer(f"🆔 ID куратора установлен: {curator_id}\n👤 Введите Ник куратора:")
        await state.set_state(AddCurator.waiting_for_nick)
    else:
        # No argument
        await message.answer("🆔 Введите ID куратора (число):")
        await state.set_state(AddCurator.waiting_for_id)

@dp.message(AddCurator.waiting_for_id)
async def process_curator_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID должен быть числом.")
        return
    await state.update_data(id=int(message.text))
    await message.answer("👤 Введите Ник куратора:")
    await state.set_state(AddCurator.waiting_for_nick)

@dp.message(AddCurator.waiting_for_nick)
async def process_curator_nick(message: Message, state: FSMContext):
    await state.update_data(nick=message.text)
    await message.answer("ℹ️ Введите информацию 'О себе':")
    await state.set_state(AddCurator.waiting_for_about)

@dp.message(AddCurator.waiting_for_about)
async def process_curator_about(message: Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer("🕰 Сколько времени работает в сфере?")
    await state.set_state(AddCurator.waiting_for_exp)

@dp.message(AddCurator.waiting_for_exp)
async def process_curator_exp(message: Message, state: FSMContext):
    await state.update_data(exp=message.text)
    await message.answer("💵 Процент с 5 профитов:")
    await state.set_state(AddCurator.waiting_for_percent)

@dp.message(AddCurator.waiting_for_percent)
async def process_curator_percent(message: Message, state: FSMContext):
    await state.update_data(percent=message.text)
    data = await state.get_data()
    
    curators.append(data)
    save_data()
    
    await message.answer(f"✅ Куратор {data['nick']} добавлен!")
    await state.clear()

# --- WORK BOT CALLBACKS ---
@dp.callback_query(F.data == "menu_work_bot")
async def work_bot_callback(callback: CallbackQuery):
    text = "🤖 <b>Ворк боты</b>\nВыберите бота для просмотра информации:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💊 NARKO", callback_data="view_narko")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "view_narko")
async def view_narko_callback(callback: CallbackQuery):
    # Placeholder data as requested
    bot_username = "@DecepShopRFbot" 
    bot_username_display = bot_username
    
    # Dynamic Ref Link
    user_id = callback.from_user.id
    ref_link = f"https://t.me/DecepShopRFbot?start={user_id}"
    
    text = (
        f"🤖 Юзернейм бота\n"
        f"┖ {bot_username_display}\n\n"
        f"Рефферальная ссылка:\n"
        f"┖ <a href='{ref_link}'><b>NARKO</b></a>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_work_bot")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Drop updates to avoid spam on restart
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
