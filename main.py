import asyncio
import logging
from aiohttp import web
from aiohttp.web_request import Request

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from keyboards import get_main_menu, get_media_menu, get_help_menu, get_admin_menu
from utils import message_counter, user_tracker, last_action_times, get_formatted_stats, SecurityUtils, TextFormatter

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ініціалізація бота і диспетчера
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Лічильники повідомлень будуть в utils.py


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Обробка команди /start"""
    try:
        welcome_text = (
            "🇺🇦 <b>Вітаємо у боті \"Дніпро ОПЕРАТИВНИЙ\"!</b> 🇺🇦\n\n"
            "📢 Тут ви можете:\n"
            "• 📸 Надсилати фото та відео\n"
            "• 📰 Ділитися новинами про стан війни\n"
            "• 🚨 Повідомляти про БпЛА та інші загрози\n"
            "• 📍 Вказувати куди що летить\n\n"
            "⚡ <b>Разом ми сильніші!</b> ⚡\n\n"
            "👇 <i>Оберіть дію з меню нижче:</i>"
        )
        
        keyboard = get_main_menu()
        await message.answer(welcome_text, reply_markup=keyboard)
        
        logger.info(f"Новий користувач: {message.from_user.id} (@{message.from_user.username})")
        
    except Exception as e:
        logger.error(f"Помилка в start_handler: {e}")
        await message.answer("❌ Виникла помилка. Спробуйте ще раз.")


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """Обробка команди /help"""
    try:
        help_text = (
            "🆘 <b>Довідка - Дніпро ОПЕРАТИВНИЙ</b>\n\n"
            "🔹 <b>Як користуватися ботом:</b>\n\n"
            "1️⃣ <b>Надсилання медіа:</b>\n"
            "   • Просто надішліть фото або відео\n"
            "   • Додайте опис до медіа\n"
            "   • Бот автоматично обробить ваше повідомлення\n\n"
            "2️⃣ <b>Текстові повідомлення:</b>\n"
            "   • Напишіть новину або інформацію\n"
            "   • Вкажіть локацію, якщо це важливо\n"
            "   • Використовуйте хештеги для категорізації\n\n"
            "3️⃣ <b>Кнопки меню:</b>\n"
            "   • 📊 Статистика - переглянути лічильники\n"
            "   • 📋 Останні повідомлення - останні новини\n"
            "   • ℹ️ Інформація - про бот та контакти\n\n"
            "⚠️ <b>Важливо:</b> Надсилайте лише перевірену інформацію!"
        )
        
        keyboard = get_help_menu()
        await message.answer(help_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Помилка в help_handler: {e}")


@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    """Адмін панель"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас немає доступу до адмін панелі.")
        return
        
    try:
        admin_text = (
            "👑 <b>Адмін панель</b>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всього повідомлень: {message_count['total']}\n"
            f"• Сьогодні: {message_count['today']}\n\n"
            "🔧 <b>Доступні дії:</b>"
        )
        
        keyboard = get_admin_menu()
        await message.answer(admin_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Помилка в admin_handler: {e}")


@dp.message(lambda message: message.content_type in ['photo', 'video'])
async def media_handler(message: types.Message):
    """Обробка фото та відео"""
    try:
        message_counter.increment()
        user_tracker.add_user(message.from_user.id)
        
        media_type = "📸 Фото" if message.content_type == 'photo' else "🎥 Відео"
        caption = message.caption or "Без опису"
        
        response_text = (
            f"✅ <b>{media_type} отримано!</b>\n\n"
            f"👤 Від: @{message.from_user.username or 'Анонім'}\n"
            f"📝 Опис: {caption}\n"
            f"🕐 Час: {message.date.strftime('%H:%M:%S')}\n\n"
            "📢 <b>Дякуємо за інформацію!</b>"
        )
        
        keyboard = get_media_menu()
        await message.answer(response_text, reply_markup=keyboard)
        
        # Лог для адміністратора
        logger.info(f"Медіа від {message.from_user.id}: {media_type}, опис: {caption}")
        
        # Повідомлення адміну (якщо потрібно)
        if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
            try:
                admin_text = (
                    f"📨 <b>Нове {media_type.lower()}</b>\n\n"
                    f"👤 Від: @{message.from_user.username or 'Анонім'} (ID: {message.from_user.id})\n"
                    f"📝 Опис: {caption}"
                )
                await bot.send_message(config.ADMIN_ID, admin_text)
                
                # Пересилка медіа адміну
                if message.content_type == 'photo':
                    await bot.send_photo(config.ADMIN_ID, message.photo[-1].file_id, caption=admin_text)
                else:
                    await bot.send_video(config.ADMIN_ID, message.video.file_id, caption=admin_text)
                    
            except Exception as admin_error:
                logger.error(f"Помилка надсилання адміну: {admin_error}")
        
    except Exception as e:
        logger.error(f"Помилка в media_handler: {e}")
        await message.answer("❌ Помилка обробки медіа. Спробуйте ще раз.")


@dp.message()
async def text_handler(message: types.Message):
    """Обробка текстових повідомлень"""
    try:
        message_counter.increment()
        user_tracker.add_user(message.from_user.id)
        
        text_content = message.text
        
        response_text = (
            "✅ <b>Повідомлення отримано!</b>\n\n"
            f"👤 Від: @{message.from_user.username or 'Анонім'}\n"
            f"📄 Текст: {text_content[:100]}{'...' if len(text_content) > 100 else ''}\n"
            f"🕐 Час: {message.date.strftime('%H:%M:%S')}\n\n"
            "📢 <b>Дякуємо за інформацію!</b>"
        )
        
        keyboard = get_media_menu()
        await message.answer(response_text, reply_markup=keyboard)
        
        logger.info(f"Текст від {message.from_user.id}: {text_content[:50]}...")
        
        # Повідомлення адміну
        if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
            try:
                admin_text = (
                    f"📝 <b>Нове текстове повідомлення</b>\n\n"
                    f"👤 Від: @{message.from_user.username or 'Анонім'} (ID: {message.from_user.id})\n"
                    f"📄 Текст: {text_content}"
                )
                await bot.send_message(config.ADMIN_ID, admin_text)
            except Exception as admin_error:
                logger.error(f"Помилка надсилання адміну: {admin_error}")
        
    except Exception as e:
        logger.error(f"Помилка в text_handler: {e}")
        await message.answer("❌ Помилка обробки повідомлення. Спробуйте ще раз.")


@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    """Обробка всіх callback запитів"""
    try:
        await callback.answer()  # Швидка відповідь для зняття підсвічування
        
        data = callback.data
        
        if data == "main_menu":
            welcome_text = (
                "🇺🇦 <b>Головне меню - Дніпро ОПЕРАТИВНИЙ</b> 🇺🇦\n\n"
                "📢 Оберіть потрібну дію:"
            )
            keyboard = get_main_menu()
            await callback.message.edit_text(welcome_text, reply_markup=keyboard)
            
        elif data == "statistics":
            stats_text = get_formatted_stats() + "\n\n📊 Статистика оновлюється в реальному часі"
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text(stats_text, reply_markup=back_keyboard)
            
        elif data == "recent_messages":
            stats = message_counter.get_stats()
            user_stats = user_tracker.get_stats()
            recent_text = (
                "📋 <b>Останні повідомлення</b>\n\n"
                "🕐 <i>За сьогодні:</i>\n"
                f"• Повідомлень: {stats['today']}\n"
                f"• Активних користувачів: {user_stats['active_today']}\n\n"
                "📊 <i>Активність зростає!</i>\n\n"
                "💡 <i>Для перегляду детальної статистики зверніться до адміністратора</i>"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text(recent_text, reply_markup=back_keyboard)
            
        elif data == "info":
            info_text = (
                "ℹ️ <b>Інформація про бот</b>\n\n"
                "🤖 <b>Дніпро ОПЕРАТИВНИЙ</b> 🇺🇦\n\n"
                "📋 <b>Призначення:</b>\n"
                "Збір та поширення оперативної інформації про події в Дніпрі та області\n\n"
                "🔧 <b>Функції:</b>\n"
                "• Прийом фото/відео матеріалів\n"
                "• Обробка текстових повідомлень\n"
                "• Швидка передача інформації\n\n"
                "📞 <b>Контакти:</b>\n"
                "• Технічна підтримка: @admin\n"
                "• Пропозиції: напишіть адміністратору\n\n"
                "⚡ <b>Слава Україні!</b> 🇺🇦"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text(info_text, reply_markup=back_keyboard)
            
        elif data == "send_new":
            send_text = (
                "📤 <b>Надсилання нового повідомлення</b>\n\n"
                "📸 Надішліть фото, відео або текст\n"
                "📝 Додайте опис до медіа\n"
                "📍 Вкажіть локацію, якщо потрібно\n\n"
                "⚡ <i>Очікую ваше повідомлення...</i>"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text(send_text, reply_markup=back_keyboard)
            
        elif data == "help":
            help_text = (
                "🆘 <b>Допомога</b>\n\n"
                "❓ <b>Як користуватися:</b>\n\n"
                "1️⃣ Надішліть фото/відео з описом\n"
                "2️⃣ Або напишіть текстове повідомлення\n"
                "3️⃣ Використовуйте кнопки для навігації\n\n"
                "💡 <b>Поради:</b>\n"
                "• Будьте точні в описах\n"
                "• Вказуйте час та місце\n"
                "• Надсилайте лише перевірену інформацію\n\n"
                "⚠️ <b>Безпека:</b> Не розголошуйте військову таємницю!"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="main_menu")]
            ])
            await callback.message.edit_text(help_text, reply_markup=back_keyboard)
            
        # Адмін функції
        elif data == "admin_stats":
            if callback.from_user.id != config.ADMIN_ID:
                await callback.answer("❌ Доступ заборонено", show_alert=True)
                return
                
            stats = message_counter.get_stats()
            user_stats = user_tracker.get_stats()
            admin_stats = (
                "👑 <b>Детальна статистика (Адмін)</b>\n\n"
                f"📊 Загальні показники:\n"
                f"• Всього повідомлень: {stats['total']}\n"
                f"• Сьогодні: {stats['today']}\n"
                f"• Всього користувачів: {user_stats['total_users']}\n"
                f"• Активні сьогодні: {user_stats['active_today']}\n\n"
                f"🔧 Системна інформація:\n"
                f"• Статус бота: ✅ Активний\n"
                f"• Webhook: ✅ Підключено\n"
                f"• Логування: ✅ Працює\n\n"
                f"📈 Продуктивність: Відмінно"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(admin_stats, reply_markup=back_keyboard)
            
        elif data == "admin_broadcast":
            if callback.from_user.id != config.ADMIN_ID:
                await callback.answer("❌ Доступ заборонено", show_alert=True)
                return
                
            broadcast_text = (
                "📢 <b>Розсилка повідомлень</b>\n\n"
                "🚧 <i>Функція в розробці</i>\n\n"
                "🔜 Незабаром буде доступна можливість:\n"
                "• Масова розсилка\n"
                "• Таргетинг по регіонах\n"
                "• Планування розсилок\n\n"
                "💡 Слідкуйте за оновленнями!"
            )
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ])
            await callback.message.edit_text(broadcast_text, reply_markup=back_keyboard)
            
        else:
            await callback.answer("❓ Невідома команда", show_alert=True)
            
    except Exception as e:
        logger.error(f"Помилка в callback_handler: {e}")
        await callback.answer("❌ Виникла помилка", show_alert=True)


async def on_startup():
    """Налаштування при запуску"""
    try:
        if config.WEBHOOK_URL:
            webhook_url = f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}"
            await bot.set_webhook(webhook_url)
            logger.info(f"Webhook встановлено: {webhook_url}")
        else:
            logger.info("Запуск в polling режимі")
        
        logger.info("Бот запущено успішно!")
        
        # Повідомлення адміну про запуск
        if config.ADMIN_ID:
            try:
                await bot.send_message(
                    config.ADMIN_ID, 
                    "🤖 <b>Бот \"Дніпро ОПЕРАТИВНИЙ\" запущено!</b>\n\n"
                    "✅ Всі системи працюють\n"
                    "📡 Готовий до прийому повідомлень"
                )
            except:
                pass
                
    except Exception as e:
        logger.error(f"Помилка при запуску: {e}")


async def on_shutdown():
    """Очищення при завершенні"""
    try:
        await bot.delete_webhook()
        logger.info("Бот зупинено")
    except Exception as e:
        logger.error(f"Помилка при зупинці: {e}")


def main():
    """Головна функція"""
    if config.WEBHOOK_URL:
        # Режим webhook для Railway
        app = web.Application()
        
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
        
        setup_application(app, dp, bot=bot)
        
        # Налаштування startup/shutdown
        async def startup_handler(app):
            await on_startup()
            
        async def cleanup_handler(app):
            await on_shutdown()
            
        app.on_startup.append(startup_handler)
        app.on_cleanup.append(cleanup_handler)
        
        web.run_app(app, host=config.WEBAPP_HOST, port=config.WEBAPP_PORT)
        
    else:
        # Режим polling для локального тестування
        async def polling():
            await on_startup()
            try:
                await dp.start_polling(bot)
            finally:
                await on_shutdown()
        
        asyncio.run(polling())


if __name__ == "__main__":
    main()