from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Головне меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics"),
            InlineKeyboardButton(text="📋 Останні повідомлення", callback_data="recent_messages")
        ],
        [
            InlineKeyboardButton(text="📤 Надіслати повідомлення", callback_data="send_new"),
            InlineKeyboardButton(text="🆘 Допомога", callback_data="help")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Інформація про бот", callback_data="info")
        ]
    ])
    return keyboard


def get_media_menu() -> InlineKeyboardMarkup:
    """Меню після отримання медіа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Надіслати ще", callback_data="send_new"),
            InlineKeyboardButton(text="📋 Останні", callback_data="recent_messages")
        ],
        [
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_help_menu() -> InlineKeyboardMarkup:
    """Меню допомоги"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Надіслати повідомлення", callback_data="send_new"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")
        ],
        [
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_admin_menu() -> InlineKeyboardMarkup:
    """Адмін меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Детальна статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📢 Розсилка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔧 Налаштування", callback_data="admin_settings"),
            InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs")
        ],
        [
            InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_confirmation_menu() -> InlineKeyboardMarkup:
    """Меню підтвердження"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Скасувати", callback_data="confirm_no")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_back_menu() -> InlineKeyboardMarkup:
    """Просте меню з кнопкою назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_navigation_menu() -> InlineKeyboardMarkup:
    """Меню навігації"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Попередня", callback_data="nav_prev"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu"),
            InlineKeyboardButton(text="➡️ Наступна", callback_data="nav_next")
        ]
    ])
    return keyboard