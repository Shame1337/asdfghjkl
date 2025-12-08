import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import json
import os
import re

# --- PERSISTENCE ---
SHOP_USERS_FILE = "shop_users.json"
shop_users = {}

def load_shop_users():
    global shop_users
    if os.path.exists(SHOP_USERS_FILE):
        with open(SHOP_USERS_FILE, "r", encoding="utf-8") as f:
            try:
                shop_users = json.load(f)
            except:
                shop_users = {}
    else:
        shop_users = {}

def save_shop_users():
    with open(SHOP_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(shop_users, f, indent=4, ensure_ascii=False)

# Load data on startup
load_shop_users()

# --- CONFIGURATION ---
TOKEN = "8279864325:AAG48LhsxzOzpDZvarttm3zgu5vSbuJn9PQ" 
ADMIN_ID = 8495992108

# --- BOT SETUP ---
from aiogram.fsm.storage.memory import MemoryStorage
dp = Dispatcher(storage=MemoryStorage())
bot = None

# --- SHOP DATA ---
# Structure: City -> [Districts] -> [Products]
# --- SHOP DATA ---
# Structure: City -> Districts -> Categories -> Products
SHOP_DATA = {
    "Москва": {
        "districts": ["Центральный", "Северный", "Южный", "Таганка"],
        "coords": {"Центральный": "active", "Северный": "active", "Южный": "active", "Таганка": "active"},
    },
    "Санкт-Петербург": {
        "districts": ["Невский", "Петроградка", "Центральный"],
        "coords": {"Невский": "active", "Петроградка": "active", "Центральный": "active"}
    },
    "Новосибирск": {
        "districts": ["Центральный", "Железнодорожный", "Калининский"],
        "coords": {"Центральный": "active", "Железнодорожный": "active", "Калининский": "active"}
    },
    "Екатеринбург": {
        "districts": ["Центральный", "Ленинский", "Октябрьский"],
        "coords": {"Центральный": "active", "Ленинский": "active", "Октябрьский": "active"}
    },
    "Казань": {
        "districts": ["Вахитовский", "Приволжский", "Советский"],
        "coords": {"Вахитовский": "active", "Приволжский": "active", "Советский": "active"}
    },
    "Красноярск": {
        "districts": ["Центральный", "Советский", "Железнодорожный"],
        "coords": {"Центральный": "active", "Советский": "active", "Железнодорожный": "active"}
    },
    "Нижний Новгород": {
        "districts": ["Нижегородский", "Канавинский", "Советский"],
        "coords": {"Нижегородский": "active", "Канавинский": "active", "Советский": "active"}
    },
    "Челябинск": {
        "districts": ["Центральный", "Ленинский", "Советский"],
        "coords": {"Центральный": "active", "Ленинский": "active", "Советский": "active"}
    },
    "Уфа": {
        "districts": ["Ленинский", "Кировский", "Советский"],
        "coords": {"Ленинский": "active", "Кировский": "active", "Советский": "active"}
    },
    "Самара": {
        "districts": ["Ленинский", "Октябрьский", "Промышленный"],
        "coords": {"Ленинский": "active", "Октябрьский": "active", "Промышленный": "active"}
    },
    "Ростов-на-Дону": {
        "districts": ["Ворошиловский", "Кировский", "Ленинский"],
        "coords": {"Ворошиловский": "active", "Кировский": "active", "Ленинский": "active"}
    },
    "Краснодар": {
        "districts": ["Центральный", "Западный", "Карасунский"],
        "coords": {"Центральный": "active", "Западный": "active", "Карасунский": "active"}
    },
    "Омск": {
        "districts": ["Центральный", "Ленинский", "Октябрьский"],
        "coords": {"Центральный": "active", "Ленинский": "active", "Октябрьский": "active"}
    },
    "Воронеж": {
        "districts": ["Центральный", "Ленинский", "Коминтерновский"],
        "coords": {"Центральный": "active", "Ленинский": "active", "Коминтерновский": "active"}
    },
    "Пермь": {
        "districts": ["Ленинский", "Свердловский", "Индустриальный"],
        "coords": {"Ленинский": "active", "Свердловский": "active", "Индустриальный": "active"}
    },
    "Волгоград": {
        "districts": ["Центральный", "Советский", "Кировский"],
        "coords": {"Центральный": "active", "Советский": "active", "Кировский": "active"}
    }
}

CATEGORIES = {
    "sedatives": "💤 Успокоительные",
    "stimulants": "💎 Кристаллы",
    "hallucinogens": "🍄 Грибы / LSD"
}

PRODUCTS = {
    "sedatives": [
        {
            "name": "💊 Метадон", "price": 3500, "weight": "0.5g", "type": "Магнит",
            "desc": "Чистейший метадон, кристально белого цвета. Качество VHQ, мощный и долгий эффект. Идеально подходит для тех, кто ценит стабильность и силу действия."
        },
        {
            "name": "🍫 Гашиш Ice O Lator", "price": 2200, "weight": "1g", "type": "Прикоп",
            "desc": "Свежайший натуральный гашиш высочайшего качества из лучших сортов шишек, никакой химии, мягкий и липкий, не крошится, потрясающий радужный аромат не оставит никого равнодушным"
        },
        {
            "name": "🥦 Шишки Runtz B52", "price": 2500, "weight": "1g", "type": "Магнит",
            "desc": "Ароматные и смолистые шишки сорта Runtz. Гибрид с преобладанием индики, обеспечивает глубокое расслабление и эйфорию. Выращено профессионалами."
        },
        {
            "name": "🥤 Сироп Wockhardt", "price": 15000, "weight": "1 fl oz", "type": "Тайник",
            "desc": "Легендарный сироп Wockhardt. Оригинальный вкус и непревзойденное качество. Редкость на рынке, эксклюзив для истинных ценителей."
        }
    ],
    "stimulants": [
        {
            "name": "⚪️ Alpha PVP Жемчужная", "price": 2800, "weight": "1g", "type": "Прикоп",
            "desc": "Жемчужные кристаллы Альфы. Мощный стимулятор, обеспечивающий прилив энергии и эйфории. Высокая степень очистки."
        },
        {
            "name": "🧊 Alpha PVP Синий лёд", "price": 2800, "weight": "1g", "type": "Тайник",
            "desc": "Крупные кристаллы цвета синего льда. Мгновенное действие и продолжительный эффект. Классика для любителей скорости."
        },
        {
            "name": "🔴 Alpha PVP Красный крис...", "price": 3000, "weight": "1g", "type": "Магнит",
            "desc": "Эксклюзивные красные кристаллы. Особая формула для более мягкого входа и долгого плато. Яркие ощущения гарантированы."
        },
        {
            "name": "❄️ Мефедрон VHQ (кристал...)", "price": 2600, "weight": "1g", "type": "Прикоп",
            "desc": "Игольчатые кристаллы Мефедрона VHQ. Эйфория, эмпатия и легкость. Идеальный выбор для отдыха в компании или соло."
        },
        {
            "name": "⚡️ Амфетамин", "price": 2000, "weight": "1g", "type": "Магнит",
            "desc": "Классический сульфат амфетамина. Ровный стим, концентрация внимания и бодрость. Отлично подходит для работы или вечеринки."
        },
        {
            "name": "💀 Экстази черепа", "price": 1500, "weight": "2 шт", "type": "Тайник",
            "desc": "Таблы в форме черепов с высоким содержанием МДМА. Чистая эйфория, мазанина и любовь ко всему миру."
        },
        {
            "name": "⬛️ Экстази Black Cube", "price": 1500, "weight": "2 шт", "type": "Прикоп",
            "desc": "Черные кубы, мощнейший приход. Только для опытных юзеров. Гарантированный улет на несколько часов."
        }
    ],
    "hallucinogens": [
        {
            "name": "🎫 Марки NBOMe", "price": 1200, "weight": "2 шт", "type": "Конверт",
            "desc": "Яркие визуалы и глубокие переживания. Путешествие в подсознание обеспечено. Соблюдайте дозировку."
        },
        {
            "name": "🐸 2CB Toad", "price": 1800, "weight": "1 шт", "type": "Тайник",
            "desc": "Психоделик нового поколения. Сочетает в себе эффекты ЛСД и МДМА. Визуалы и эмпатия в одном флаконе."
        }
    ]
}




PAYMENT_METHODS = {
    "BTC": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "LTC": "ltc1q5wmr9a37458739938475893475893475",
    "Card": "4400 0000 0000 0000"
}

# --- STATES ---
class PaymentState(StatesGroup):
    waiting_for_amount = State()

class MammothState(StatesGroup):
    waiting_for_balance = State()
    waiting_for_discount = State()
    target_mammoth_id = State()

# --- HANDLERS ---

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Unknown"
    
    # Referral Logic
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        referrer_id = args[1]
        
    # Register user if new
    load_shop_users()
    if user_id not in shop_users:
        shop_users[user_id] = {
            "username": username,
            "balance": 0,
            "discount": 0,
            "orders": 0,
            "referrer_id": referrer_id, 
            "join_date": str(message.date),
            "terms_accepted": False
        }
        save_shop_users()
        
        # Notify Referrer
        if referrer_id:
             try:
                 if bot:
                    await bot.send_message(
                        chat_id=referrer_id, 
                        text=f"� <b>Новый мамонт!</b>\n@{username} (ID: {user_id})\nУправление: /m_{user_id}"
                    )
             except Exception as e:
                 logging.error(f"Failed to notify referrer: {e}")

    # Terms & Conditions (skipped for redesign request to jump straight to menu, 
    # but keeping logic if needed. For now, let's just show menu directly 
    # as the user asked for design changes primarily)
    
    # Send the pill emoji first as requested
    await message.answer("�")
    
    await show_main_menu(message)


@dp.callback_query(F.data == "view_menu")
async def view_menu_callback(callback: CallbackQuery):
    # Set terms accepted when user clicks accept button
    user_id = str(callback.from_user.id)
    load_shop_users()
    if user_id in shop_users:
        shop_users[user_id]["terms_accepted"] = True
        save_shop_users()
    
    await show_main_menu(callback)

@dp.callback_query(F.data == "view_support")
async def support_callback(callback: CallbackQuery):
    await callback.answer("🆘 Служба поддержки: @DecepSupport\nМы работаем 24/7", show_alert=True)

@dp.callback_query(F.data == "view_reviews")
async def reviews_callback(callback: CallbackQuery):
    await callback.answer("⭐️ Отзывы клиентов\nВсего отзывов: 1,337\nСредний рейтинг: 4.9/5", show_alert=True)

@dp.callback_query(F.data == "view_referral")
async def referral_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    load_shop_users()
    # Mock earnings
    earnings = 0
    
    text = (
        "👥 <b>Реферальная программа</b> 👥\n\n"
        f"Ваша реферальная ссылка: {ref_link}\n\n"
        f"▪️ Заработано за всё время: {earnings} ₽\n\n"
        "Если человек, приглашенный по реферальной ссылке, пополнит баланс, то вы получите 10% от суммы его депозита"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]]
    
    photo_path = "images/referral.jpg"
    if not os.path.exists(photo_path): photo_path = "images/menu.jpg"
    
    try:
        if os.path.exists(photo_path):
             photo = FSInputFile(photo_path)
             await callback.message.edit_media(
                 media=types.InputMediaPhoto(media=photo, caption=text),
                 reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
             )
        else:
             await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
             await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
             await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "add_balance")
async def add_balance_callback(callback: CallbackQuery, state: FSMContext):
    text = "💳 Введите сумму для депозита:"
    buttons = [[InlineKeyboardButton(text="🔙 Отмена", callback_data="view_menu")]]
    
    # We need to transition to input mode. 
    # Usually editing the message is best, but we are waiting for text input.
    # We can delete/edit and ask for input.
    
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(PaymentState.waiting_for_amount)
    await callback.answer()

@dp.message(PaymentState.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число!")
        return
        
    amount = int(message.text)
    if amount < 3000:
        await message.answer("❌ Минимальная сумма пополнения - 3000 RUB!")
        return

    await state.update_data(deposit_amount=amount)
    
    text = (
        f"💳 Сумма депозита: {amount} RUB\n"
        "💳 Выберите способ оплаты:"
    )
    
    buttons = [
        [InlineKeyboardButton(text="💳 Банковская карта ( анонимно )", callback_data="pay_method_card")],
        [InlineKeyboardButton(text="👨‍💻 Пополнить через оператора", callback_data="pay_method_operator")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]
    ]
    
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    # We don't verify strict state here as we move to button click, but generally good practice to clear or keep state if needed.
    # Let's clear state as next steps are button presses.
    await state.clear()

@dp.callback_query(F.data == "pay_method_card")
async def pay_card_callback(callback: CallbackQuery):
    text = (
        "💳 <b>Оплата банковской картой</b>\n\n"
        "Для пополнения баланса на карту, пожалуйста, обратитесь в техническую поддержку.\n\n"
        "Наши специалисты помогут вам быстро провести платёж и ответят на все вопросы.\n\n"
        "💬 <b>Поддержка работает круглосуточно</b>"
    )
    
    buttons = [
        [InlineKeyboardButton(text="💬 Перейти в поддержку", url="https://t.me/DecepSupport")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]
    ]
    
    # Try edit
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), disable_web_page_preview=True)
    except:
        try:
             # Just in case previous msg had media
             await callback.message.delete()
             await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), disable_web_page_preview=True)
        except:
             pass
    await callback.answer()

@dp.callback_query(F.data == "pay_method_operator")
async def pay_operator_callback(callback: CallbackQuery):
    text = (
        "👨‍💻 <b>Пополнение через оператора</b>\n\n"
        "За получением реквизитов для оплаты обратитесь к оператору\n\n"
        "Контакт оператора - @DecepSupport"
    )
    
    buttons = [
         [InlineKeyboardButton(text="💬 Перейти к оператору", url="https://t.me/DecepSupport")],
         [InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]
    ]
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

async def show_main_menu(message_input):
    # Handles both Message and CallbackQuery
    if isinstance(message_input, Message):
        msg = message_input
        edit = False
    else:
        msg = message_input.message
        edit = True
        
    text = (
        "⚡️ Добро пожаловать в  <b>Отдых PRO (DECEP)</b>\n"
        "@DecepShopRFbot ⚡️\n\n"
        "▪️ В нашем магазине в короткие сроки вы можете получить необходимый вам товар.\n"
        "▪️ Мы работаем круглосуточно.\n"
        "▪️ Всегда сверяйте юзернейм оператора. МЫ НИКОГДА НЕ НАПИШЕМ ПЕРВЫЕ.\n"
        "▪️ Если ваш населённый пункт отсутствует в каталоге - обратитесь к оператору, мы поможем с оформлением предзаказа/доставки"
    )
    
    buttons = [
        [
            InlineKeyboardButton(text="🛍 Каталог", callback_data="view_catalog_0"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="view_profile"),
            InlineKeyboardButton(text="ℹ️ Инфо", callback_data="view_info")
        ],
        [
            InlineKeyboardButton(text="📦 Мои покупки", callback_data="history"),
            InlineKeyboardButton(text="🚚 Доставка", callback_data="view_delivery")
        ],
        [
            InlineKeyboardButton(text="⭐️ Избранное", callback_data="view_favorites"),
            InlineKeyboardButton(text="⏱ Недавние", callback_data="view_recent")
        ],
        [
            InlineKeyboardButton(text="🔥 Работа", callback_data="worker"),
            InlineKeyboardButton(text="👨‍💻 Оператор", url="https://t.me/DecepSupport")
        ],
        [
             InlineKeyboardButton(text="🤝 Реферальная система", callback_data="view_referral")
        ],
        [
            InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="add_balance")
        ]
    ]

    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Check for both logic
    photo_path = "images/menu.jpg"
    if not os.path.exists(photo_path):
        photo_path = "images/menu.png"
        
    if edit:
        # For edits, try to edit media if photo exists
        if os.path.exists(photo_path):
            try:
                photo = FSInputFile(photo_path)
                await msg.edit_media(
                    media=types.InputMediaPhoto(media=photo, caption=text),
                    reply_markup=keyboard
                )
            except:
                # If edit fails, delete and send new
                try:
                    await msg.delete()
                    photo = FSInputFile(photo_path)
                    await msg.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
                except:
                    await msg.answer(text, reply_markup=keyboard)
        else:
            try:
                await msg.edit_text(text, reply_markup=keyboard)
            except:
                await msg.delete()
                await msg.answer(text, reply_markup=keyboard)
    else:
        # For new messages, send with photo if available
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await msg.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
        else:
            await msg.answer(text, reply_markup=keyboard)

async def show_catalog_page(callback: CallbackQuery, page: int):
    cities = list(SHOP_DATA.keys())
    ITEMS_PER_PAGE = 4 
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_cities = cities[start_idx:end_idx]
    
    buttons = []
    
    # Cities Grid (2 per row)
    city_row = []
    for city in current_cities:
        city_row.append(InlineKeyboardButton(text=f"📍 {city}", callback_data=f"city_{city}"))
        if len(city_row) == 2:
            buttons.append(city_row)
            city_row = []
    if city_row:
        buttons.append(city_row)
    
    # Navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"view_catalog_{page-1}"))
    
    # Page indicator
    total_pages = (len(cities) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="ignore"))

    if end_idx < len(cities):
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"view_catalog_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
        
    buttons.append([InlineKeyboardButton(text="« Главное меню", callback_data="view_menu")])

    text = "🏙 <b>Выберите город:</b>"
    
    photo_path = "images/catalog.jpg"
    if not os.path.exists(photo_path):
        photo_path = "images/catalog.png"
    try:
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await callback.message.edit_media(
                media=types.InputMediaPhoto(media=photo, caption=text),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        else:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        # If edit fails, delete and send new
        try:
            await callback.message.delete()
            if os.path.exists(photo_path):
                photo = FSInputFile(photo_path)
                await callback.message.answer_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            else:
                await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
            pass
    
    try:
        await callback.answer()
    except:
        pass

@dp.callback_query(F.data == "view_profile")
async def profile_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    username = callback.from_user.username or "Аноним"
    
    load_shop_users()
    user_info = shop_users.get(user_id, {"balance": 0, "orders": 0, "discount": 0})
    
    # Calculate registration date if available, else use "Unknown"
    join_date = user_info.get("join_date", "Неизвестно")
    # Format date if it's a timestamp string? Usually it's raw string from str(message.date)
    # Let's keep it simple or try to parse if needed. For now raw string is fine or simple format.
    # The screenshot shows "12/8/2025". Let's try to format if it looks like a datetime.
    try:
        # If it's standard telegram date string, it might need parsing. 
        # But we stored it as str(message.date). Let's just assume it's readable enough or keep as is.
        pass
    except:
        pass

    chat_link = "https://t.me/+2Tz6f482I59mZjIyzz" if user_info.get("orders", 0) >= 5 else "Для доступа к чату необходимо сделать 5 заказов"
    
    text = (
        f"💊 <b>Ваш профиль</b> 💊\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"👤 Логин: @{username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"� Количество заказов: {user_info.get('orders', 0)}\n"
        f"⚖️ Диспуты: 0\n\n"
        f"� Баланс: {user_info.get('balance', 0)} ₽\n\n"
        f"� Дата регистрации: {join_date}\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"Ссылка на чат: {chat_link}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="� Пополнить баланс", callback_data="add_balance")],
        [InlineKeyboardButton(text="📜 История заказов", callback_data="history")],
        [InlineKeyboardButton(text="« Главное меню", callback_data="view_menu")]
    ])
    
    photo_path = "images/profile.jpg"
    if not os.path.exists(photo_path):
        photo_path = "images/profile.png"
    
    # Try to edit existing message
    try:
        if os.path.exists(photo_path):
            # Edit with new photo
            photo = FSInputFile(photo_path)
            await callback.message.edit_media(
                media=types.InputMediaPhoto(media=photo, caption=text),
                reply_markup=keyboard
            )
        else:
            # Try to edit text or caption
            try:
                await callback.message.edit_text(text, reply_markup=keyboard)
            except:
                # If message has photo, edit caption instead
                await callback.message.edit_caption(caption=text, reply_markup=keyboard)
    except Exception as e:
        # If all edits fail, delete and send new
        try:
            await callback.message.delete()
        except:
            pass
        
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await callback.message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
        else:
            await callback.message.answer(text, reply_markup=keyboard)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("city_"))
async def city_callback(callback: CallbackQuery):
    city_name = callback.data.split("_")[1]
    districts = SHOP_DATA[city_name]["districts"]
    
    buttons = []
    # 2 columns for districts
    row = []
    for dist in districts:
        row.append(InlineKeyboardButton(text=f"📍 {dist}", callback_data=f"dist_{city_name}_{dist}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="view_catalog_0")])
    
    text = (
        f"📍 <b>{city_name}</b>\n"
        f"🚚 Доставка по всему городу\n\n"
        f"Выберите район:"
    )
    
    # Try to edit message (handle both text and photo messages)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        # If message has photo, edit caption instead
        try:
            await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
            pass
    
    await callback.answer()

@dp.callback_query(F.data.startswith("dist_"))
async def district_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    city_name = parts[1]
    district_name = parts[2]
    
    # Check emptiness
    status = SHOP_DATA[city_name]["coords"].get(district_name, "active")
    if status == "empty":
       await callback.answer("❌ В данном районе нет курьеров или товара.", show_alert=True)
       return

    # Show Categories
    text = f"📍 <b>{city_name} / {district_name}</b>\nВыберите категорию:"
    buttons = []
    
    for cat_key, cat_name in CATEGORIES.items():
        buttons.append([InlineKeyboardButton(text=cat_name, callback_data=f"cat_{city_name}_{district_name}_{cat_key}")])
        
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"city_{city_name}")])
    
    # Try to edit message (handle both text and photo messages)
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
            pass
    
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def category_callback(callback: CallbackQuery):
    # cat_City_Dist_Category
    parts = callback.data.split("_")
    city_name = parts[1]
    district_name = parts[2]
    cat_key = parts[3]
    
    products = PRODUCTS.get(cat_key, [])
    
    buttons = []
    for idx, prod in enumerate(products):
        buttons.append([
            InlineKeyboardButton(
                text=f"{prod['name']} - {prod['price']} RUB", 
                callback_data=f"prod_{city_name}_{district_name}_{cat_key}_{idx}"
            )
        ])
        
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"dist_{city_name}_{district_name}")])
    
    text = f"🛍 <b>Категория: {CATEGORIES[cat_key]}</b>\nВыберите товар:"
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
            pass
    
    await callback.answer()

@dp.callback_query(F.data.startswith("prod_"))
async def product_callback(callback: CallbackQuery):
    # prod_City_Dist_Category_Index
    parts = callback.data.split("_")
    city_name = parts[1]
    district_name = parts[2]
    cat_key = parts[3]
    prod_idx = int(parts[4])
    
    product = PRODUCTS[cat_key][prod_idx]
    
    # Description fallback
    desc = product.get("desc", "Описание отсутствует.")
    p_type = product.get("type", "Тайник")
    
    # Random wait to simulate loading or just instant
    
    text = (
        f"<b>{product['name']}</b>\n\n"
        f"<i>{desc}</i>\n\n"
        f"🏙 <b>Город:</b> 🏙 {city_name}\n"
        f"� <b>Район:</b> 💠 {district_name}\n"
        f"📦 <b>Позиция:</b> 💊 {product['weight']} | {p_type}\n"
        f"💰 <b>Цена:</b> {product['price']}₽\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"✔️ <i>Выберите доступный бонус-код по кнопке ниже или нажмите</i> <b>'нет бонус-кода'</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"
    )
    
    buttons = [
        [InlineKeyboardButton(text="✅ Всё верно", callback_data=f"prebuy_{city_name}_{district_name}_{cat_key}_{prod_idx}")],
        [
            InlineKeyboardButton(text="⭐️ В избранное", callback_data=f"fav_{cat_key}_{prod_idx}"),
            InlineKeyboardButton(text="🆚 Сравнить", callback_data=f"compare_{cat_key}_{prod_idx}")
        ],
        [InlineKeyboardButton(text="🔔 Уведомить: если подешевеет", callback_data=f"notify_price_{cat_key}_{prod_idx}")],
        [InlineKeyboardButton(text="🔔 Уведомить: когда появится", callback_data=f"notify_stock_{cat_key}_{prod_idx}")],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{city_name}_{district_name}_{cat_key}"),
            InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="view_menu")
        ]
    ]
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
             await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
             try:
                 await callback.message.delete()
                 await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
             except:
                 pass
    
    await callback.answer()

@dp.callback_query(F.data.startswith("prebuy_"))
async def prebuy_callback(callback: CallbackQuery):
    # prebuy_City_Dist_Category_Index
    parts = callback.data.split("_")
    cat_key = parts[3]
    prod_idx = int(parts[4])
    
    product = PRODUCTS[cat_key][prod_idx]
    
    text = (
        f"💳 <b>Выберите способ оплаты</b>\n"
        f"Сумма к оплате: {product['price']} RUB"
    )
    
    buttons = [
        [InlineKeyboardButton(text="💎 Bitcoin (BTC)", callback_data=f"pay_BTC_{product['price']}")],
        [InlineKeyboardButton(text="Ł LiteCoin (LTC)", callback_data=f"pay_LTC_{product['price']}")],
        [InlineKeyboardButton(text="💳 Карта (RUB)", callback_data=f"pay_Card_{product['price']}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback.data.replace("prebuy_", "prod_"))]
    ]
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("fav_"))
async def add_fav_callback(callback: CallbackQuery):
    await callback.answer("⭐️ Товар добавлен в избранное", show_alert=False)

@dp.callback_query(F.data.startswith("compare_"))
async def compare_callback(callback: CallbackQuery):
    await callback.answer("🆚 Товар добавлен к сравнению", show_alert=False)

@dp.callback_query(F.data.startswith("notify_"))
async def notify_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1] # price or stock
    if action == "price":
        await callback.answer("🔔 Вы получите уведомление, если цена снизится на 10-20%", show_alert=True)
    else:
        await callback.answer("🔔 Вы получите уведомление, когда товар появится в наличии", show_alert=True)

# --- WORKER & VACANCIES ---

@dp.callback_query(F.data == "worker")
async def worker_callback(callback: CallbackQuery):
    text = (
        "🔥 <b>Работа</b> 🔥\n\n"
        "Свободные вакансии в нашем магазине:"
    )
    
    buttons = [
        [
            InlineKeyboardButton(text="🏃 Курьер", callback_data="vac_courier"),
            InlineKeyboardButton(text="🖼 Трафаретчик", callback_data="vac_stencil"),
            InlineKeyboardButton(text="🚛 Водитель", callback_data="vac_driver")
        ],
        [
            InlineKeyboardButton(text="📰 Верификация", callback_data="vac_verification"),
            InlineKeyboardButton(text="👨‍💻 Оператор", callback_data="vac_operator")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]
    ]
    
    # Try different photos if available, or just keeping the menu photo or changing it?
    # The screenshot shows a specific image for work. Let's try to use 'work.jpg' if it exists, else menu image.
    photo_path = "images/work.jpg" 
    if not os.path.exists(photo_path):
        photo_path = "images/menu.jpg"
        
    try:
        if os.path.exists(photo_path):
             # Force new photo if switching from menu to work
            photo = FSInputFile(photo_path)
            await callback.message.edit_media(
                media=types.InputMediaPhoto(media=photo, caption=text),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        else:
             await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
             await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
             
    await callback.answer()

@dp.callback_query(F.data == "vac_courier")
async def vac_courier(callback: CallbackQuery):
    text = (
        "🏃‍♂️ <b>Курьер</b> 🏃‍♂️\n\n"
        "Суть работы - «раскладка» позиций по выданному району.\n\n"
        "▪️ Мы платим за загруженные адреса, вам не нужно ожидать продажи клада.\n"
        "▪️ Оплата за выполненную работу день в день.\n"
        "▪️ Премии и бонусы среди курьеров организуются еженедельно.\n"
        "▪️ Конкурсы среди курьеров проводятся в конце каждого календарного месяца.\n"
        "▪️ Мы обладаем огромной библиотекой обучающих материалов. Обучение проводится сотрудниками со стажем работы более пяти лет.\n"
        "▪️ Присутствует чат для курьеров, в котором вы сможете обмениваться опытом с другими сотрудниками.\n\n"
        "<i>Устройство исключительно по залогу от 3000₽. Для начала трудоустройства напишите свой город оператору.</i>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="worker")]]
    await _edit_vacancy_text(callback, text, buttons)

@dp.callback_query(F.data == "vac_stencil")
async def vac_stencil(callback: CallbackQuery):
    text = (
        "� <b>Трафаретчик</b> 🖼\n\n"
        "Суть работы - нанесение рисунка/наклейки на проходимые места, фотографирование граффити/стикера через приложение NoteCam\n\n"
        "▪️ Оплата от 110₽ за граффити.\n"
        "▪️ Оплата от 50₽ за стикер.\n"
        "▪️ Выплата от 20 граффити / 50 стикеров.\n"
        "▪️ Текст для граффити выдаст оператор.\n"
        "▪️ Чек при покупке краски сохраняйте, мы компенсируем затраты на неё при получении первой ЗП.\n\n"
        "<i>Для начала трудоустройства напишите свой город оператору, получите более подробную информацию и купите баллон с краской.</i>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="worker")]]
    await _edit_vacancy_text(callback, text, buttons)

@dp.callback_query(F.data == "vac_driver")
async def vac_driver(callback: CallbackQuery):
    text = (
        "🚛 <b>Водитель</b> 🚛\n\n"
        "Суть работы - перевозка товара (хим.веществ нелегального характера между городами)\n\n"
        "График не нормирован, рейсы на разные расстояния, ЗП от 70000₽ за рейс, работа с большим весом..\n"
        "▪️ Все расходные материалы покрывают отдельно (ГСМ, аренда жилья по надобности).\n"
        "▪️ Оплату получаете после доставки товара, и его проверки, все расходы так же возмещают в ЗП.\n"
        "▪️ ЗП на биткоин кошелек, в случае неумения им пользоваться - предоставляется инструкция.\n"
        "▪️ После устройства куратор проведет полный инструктаж по работе и технике безопасности, для практики вам будет выдан один оплачиваемый стажировочный рейс.\n\n"
        "<i>Устройство исключительно по залогу от 60000₽. Для начала трудоустройства напишите свой город оператору.</i>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="worker")]]
    await _edit_vacancy_text(callback, text, buttons)

@dp.callback_query(F.data == "vac_verification")
async def vac_verification(callback: CallbackQuery):
    text = (
        "📰 <b>Верификация</b> 📰\n\n"
        "Суть работы - прохождение верификации на различных биржах\n\n"
        "▪️ Доступно от 2х заданий ежедневно.\n"
        "▪️ Выплата после проверки документа сервисом.\n"
        "▪️ Оплата 1 задания = 1000 ₽.\n"
        "▪️ Оплату за верификацию можно использовать как залог для другой вакансии.\n\n"
        "<i>Для начала трудоустройства пришлите фото первой страницы паспорта оператору. Пример:</i> <a href='https://telegra.ph/file/52e526bf246fbd07eb5e5.png'>перейти</a>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="worker")]]
    await _edit_vacancy_text(callback, text, buttons)

@dp.callback_query(F.data == "vac_operator")
async def vac_operator(callback: CallbackQuery):
    text = (
        "👨‍💻 <b>Оператор</b> 👨‍💻\n\n"
        "Суть работы - прием оплаты от клиентов, консультация, выдача координатов.\n\n"
        "▪️ График - самостоятельный (5/2, 2/2 и т.д. на ваше усмотрение).\n"
        "▪️ Минимальное время работы в день - 4 часа, но не менее 30ч в неделю.\n"
        "▪️ ЗП рассчитывается от % выполненных продаж + премии.\n"
        "▪️ % от продаж рассчитывается в зависимости от времени суток. Дневное время - 5%, ночное - 10%.\n"
        "▪️ Необходим навык быстрого набора текста без допущения орфографических ошибок.\n\n"
        "<i>Устройство исключительно по залогу от 5000₽. Для начала трудоустройства напишите свой город оператору.</i>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="worker")]]
    await _edit_vacancy_text(callback, text, buttons)

async def _edit_vacancy_text(callback, text, buttons):
    try:
        await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        except:
            await callback.message.delete()
            photo_path = "images/work.jpg"
            if not os.path.exists(photo_path): photo_path = "images/menu.jpg"
            
            if os.path.exists(photo_path):
                 photo = FSInputFile(photo_path)
                 await callback.message.answer_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            else:
                 await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.message(Command("worker"))
async def cmd_worker(message: Message):
    # Just redirect to callback logic by sending a new message with work menu
    text = (
        "🔥 <b>Работа</b> 🔥\n\n"
        "Свободные вакансии в нашем магазине:"
    )
    buttons = [
         [
            InlineKeyboardButton(text="🏃 Курьер", callback_data="vac_courier"),
            InlineKeyboardButton(text="🖼 Трафаретчик", callback_data="vac_stencil"),
            InlineKeyboardButton(text="🚛 Водитель", callback_data="vac_driver")
        ],
        [
            InlineKeyboardButton(text="📰 Верификация", callback_data="vac_verification"),
            InlineKeyboardButton(text="👨‍💻 Оператор", callback_data="vac_operator")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]
    ]
    
    photo_path = "images/work.jpg"
    if not os.path.exists(photo_path):
         photo_path = "images/menu.jpg"
         
    if os.path.exists(photo_path):
         photo = FSInputFile(photo_path)
         await message.answer_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
         await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))



@dp.message(F.text.regexp(r"^/m_(\d+)$"))
async def cmd_manage_mammoth(message: Message, state: FSMContext):
    match = re.match(r"^/m_(\d+)$", message.text)
    if not match: return
    
    target_id = match.group(1)
    
    # Reload data
    load_shop_users()
    mammoth = shop_users.get(target_id)
    
    if not mammoth:
        await message.answer("❌ Мамонт не найден.")
        return
        
    # Verify ownership (optional, but good)
    if str(mammoth.get("referrer_id")) != str(message.from_user.id):
        await message.answer("❌ Это не твой мамонт.")
        return

    text = (
        f"🦣 <b>Управление мамонтом</b>\n"
        f"👤: @{mammoth.get('username')}\n"
        f"🆔: <code>{target_id}</code>\n"
        f"💰 Баланс: {mammoth.get('balance')} RUB\n"
        f"🏷 Скидка: {mammoth.get('discount')}%\n"
        f"📅 Рег: {mammoth.get('join_date')}"
    )
    
    buttons = [
        [InlineKeyboardButton(text="💰 Изменить баланс", callback_data=f"edit_m_bal_{target_id}")],
        [InlineKeyboardButton(text="🏷 Создать промокод (Скидка)", callback_data=f"edit_m_disc_{target_id}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_panel")]
    ]
    
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "close_panel")
async def close_panel(callback: CallbackQuery):
    await callback.message.delete()

@dp.callback_query(F.data.startswith("edit_m_bal_"))
async def edit_bal_start(callback: CallbackQuery, state: FSMContext):
    tid = callback.data.split("_")[3]
    await state.update_data(mid=tid)
    await callback.message.answer("💰 Введите новый баланс (число):")
    await state.set_state(MammothState.waiting_for_balance)
    await callback.answer()

@dp.message(MammothState.waiting_for_balance)
async def edit_bal_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Число!")
        return
    data = await state.get_data()
    tid = data.get("mid")
    
    shop_users[tid]["balance"] = int(message.text)
    save_shop_users()
    await message.answer(f"✅ Баланс изменен на {message.text}")
    await state.clear()

@dp.callback_query(F.data.startswith("edit_m_disc_"))
async def edit_disc_start(callback: CallbackQuery, state: FSMContext):
    tid = callback.data.split("_")[3]
    await state.update_data(mid=tid)
    await callback.message.answer("🏷 Введите скидку в % (0-100):")
    await state.set_state(MammothState.waiting_for_discount)
    await callback.answer()

@dp.message(MammothState.waiting_for_discount)
async def edit_disc_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Число!")
        return
    data = await state.get_data()
    tid = data.get("mid")
    
    shop_users[tid]["discount"] = int(message.text)
    save_shop_users()
    await message.answer(f"✅ Скидка установлена: {message.text}%")
    await state.clear()


@dp.callback_query(F.data.startswith("pay_"))
async def payment_callback(callback: CallbackQuery):
    # Format: pay_Method_Amount
    parts = callback.data.split("_")
    method = parts[1]
    raw_amount = int(parts[2])
    
    user_id = str(callback.from_user.id)
    load_shop_users()
    discount = shop_users.get(user_id, {}).get("discount", 0)
    
    # Apply discount
    amount = raw_amount
    if discount > 0:
        amount = int(raw_amount * (1 - discount/100))
    
    wallet = PAYMENT_METHODS.get(method, "Error")
    
    text = (
        f"💳 <b>Оплата: {method}</b>\n\n"
        f"Сумма: <s>{raw_amount}</s> <b>{amount} RUB</b> (Скидка {discount}%)\n"
        f"Реквизиты: <code>{wallet}</code>\n\n"
        f"⚠️ У вас есть 30 минут на оплату.\n"
        f"После перевода нажмите 'Проверить оплату'."
    )
    
    buttons = [
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="view_menu")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "check_payment")
async def check_payment_callback(callback: CallbackQuery):
    await callback.answer("⏳ Проверяем транзакцию...", show_alert=False)
    # Simulate loading
    await asyncio.sleep(2)
    await callback.answer("❌ Оплата не найдена. Попробуйте через минуту.", show_alert=True)

@dp.callback_query(F.data.startswith("view_catalog_"))
async def catalog_callback_handler(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await show_catalog_page(callback, page)

@dp.callback_query(F.data == "view_info")
async def info_callback(callback: CallbackQuery):
    text = (
        "ℹ️ <b>Информация</b> ℹ️\n\n"
        "Мы - команда профессионалов, работающая на рынке более 5 лет.\n"
        "Наш магазин гарантирует высокое качество товара и безопасность сделок.\n\n"
        "🚚 <b>Доставка:</b>\n"
        "Мы осуществляем доставку по всем крупным городам РФ.\n"
        "Среднее время доставки - 2 часа.\n\n"
        "🛡 <b>Гарантии:</b>\n"
        "Если вы не нашли клад, мы сделаем перезаклад за наш счет (при наличии доказательств).\n\n"
        "⭐️ <a href='@ХУЙ'>Отзывы о нас</a>"
    )
    buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="view_menu")]]
    
    try:
         await callback.message.edit_caption(caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except:
         try:
             await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
         except:
             await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data == "history")
async def history_callback(callback: CallbackQuery):
    await callback.answer("🛒 История покупок не найдена.", show_alert=True)

@dp.callback_query(F.data == "view_delivery")
async def delivery_callback(callback: CallbackQuery):
    await callback.answer("🚖 Доставка работает в штатном режиме.", show_alert=True)

@dp.callback_query(F.data == "view_favorites")
async def favorites_callback(callback: CallbackQuery):
    await callback.answer("⭐️ Избранное пусто.", show_alert=True)

@dp.callback_query(F.data == "view_recent")
async def recent_callback(callback: CallbackQuery):
    await callback.answer("⏱ Недавние товары отсутствуют.", show_alert=True)

async def main():
    global bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
