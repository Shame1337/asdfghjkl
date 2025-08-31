import telebot
import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import Flask, request
import threading
import logging

# Consolidated imports from config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
AI_API_KEY = os.getenv('AI_API_KEY', 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjBmMjc2NjJhLWVhMGUtNGRlZC05MDQ1LTcyNzJiNWI4ZjZlNyIsImV4cCI6NDkxMDI1MzU5Mn0.P1IFARUejNIkl9RbQ7Ynpp-CZZegzYo3ed7ynRGCBrgvWp6ZcaaSoIKUUMjBADlojgLmOQZXC6uMxagqrIsjew')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# AI API settings
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
AI_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

# Railway settings
PORT = int(os.getenv('PORT', 5000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Subscription settings
DAILY_FREE_MESSAGES = 20
SUBSCRIPTION_PLANS = {
    '1month': {'name': '1 месяц', 'price': '200₴', 'duration_days': 30},
    '6months': {'name': '6 месяцев', 'price': '1000₴', 'duration_days': 180},
    '12months': {'name': '12 месяцев', 'price': '1800₴', 'duration_days': 365},
    'lifetime': {'name': 'Навсегда', 'price': '3999₴', 'duration_days': -1}
}

# Роли AI
AI_ROLES = {
    'cortex': {'name': '🤖 CortexaAI', 'prompt_file': 'prompts/cortex_standard.txt', 'description': 'Стандартный умный помощник'},
    'boy': {'name': '😎 Парень', 'prompt_file': 'prompts/ai_boy.txt', 'description': 'Крутой виртуальный друг'},
    'girl': {'name': '💕 Девушка', 'prompt_file': 'prompts/ai_girl.txt', 'description': 'Милая виртуальная подружка'},
    'hacker': {'name': '💰 Темщик', 'prompt_file': 'prompts/ai_hacker.txt', 'description': 'Лютый темщик'},
    'nerd': {'name': '🤓 Душнила', 'prompt_file': 'prompts/ai_nerd.txt', 'description': 'Умный ботаник-всезнайка'}
}

# Check required variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize Flask app for webhook
app = Flask(__name__)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("✅ Конфигурация загружена успешно!")
print(f"🤖 Порт для деплоя: {PORT}")
print(f"🔗 Webhook URL: {WEBHOOK_URL}")


class AIClient:
    """Клиент для работы с Intelligence.io API"""
    
    def __init__(self):
        self.api_url = AI_API_URL
        self.api_key = AI_API_KEY
        self.model = AI_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.system_prompt = self.load_system_prompt()
        self.role_prompts = self.load_role_prompts()
    
    def load_system_prompt(self) -> str:
        """Загружает стандартный системный промпт"""
        try:
            with open('system_prompt.txt', 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            logger.info("✅ Системный промпт загружен из файла")
            return prompt
        except FileNotFoundError:
            logger.warning("⚠️ Файл system_prompt.txt не найден, используется стандартный промпт")
            return "Ты умный и дружелюбный AI-ассистент. Отвечай на русском языке кратко и с эмодзи."
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки system_prompt.txt: {str(e)}")
            return "Ты умный и дружелюбный AI-ассистент. Отвечай на русском языке кратко и с эмодзи."
    
    def load_role_prompts(self) -> dict:
        """Загружает промпты для всех ролей"""
        prompts = {}
        for role_key, role_info in AI_ROLES.items():
            try:
                with open(role_info['prompt_file'], 'r', encoding='utf-8') as f:
                    prompts[role_key] = f.read().strip()
                logger.info(f"✅ Промпт для роли {role_key} загружен")
            except FileNotFoundError:
                logger.warning(f"⚠️ Промпт для роли {role_key} не найден")
                prompts[role_key] = self.system_prompt
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки промпта {role_key}: {str(e)}")
                prompts[role_key] = self.system_prompt
        return prompts
    
    def get_role_prompt(self, role: str) -> str:
        """Получает промпт для указанной роли"""
        return self.role_prompts.get(role, self.system_prompt)
    
    def chat_completion(self, messages: List[Dict[str, str]], user_role: str = 'cortex', include_system: bool = True) -> Optional[str]:
        """Отправляет запрос к AI API и возвращает ответ"""
        try:
            full_messages = []
            
            if include_system:
                role_prompt = self.get_role_prompt(user_role)
                full_messages.append({
                    "role": "system",
                    "content": role_prompt
                })
            
            full_messages.extend(messages)
            
            data = {
                "model": self.model,
                "messages": full_messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"❌ Неожиданный формат ответа: {result}")
                    return "🤖 Извините, получен неожиданный ответ от AI"
            else:
                logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                return f"🤖 Ошибка AI сервиса: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("❌ Таймаут запроса к AI API")
            return "🤖 Извините, AI сервис не отвечает. Попробуйте позже."
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ Ошибка подключения к AI API")
            return "🤖 Проблемы с подключением к AI сервису."
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {str(e)}")
            return "🤖 Произошла ошибка при обработке запроса."


class UserManager:
    """Управление пользователями и подписками"""
    
    def __init__(self):
        self.data_file = "users_data.json"
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """Создает файл данных если его нет"""
        if not os.path.exists(self.data_file):
            self.save_data({})
            logger.info(f"📁 Создан файл данных: {self.data_file}")
    
    def load_data(self) -> Dict[str, Any]:
        """Загружает данные пользователей"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Ошибка загрузки данных: {str(e)}")
            return {}
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Сохраняет данные пользователей"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"❌ Ошибка сохранения данных: {str(e)}")
            return False
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Получает данные пользователя"""
        data = self.load_data()
        user_key = str(user_id)
        
        if user_key not in data:
            data[user_key] = self.create_default_user(user_id)
            self.save_data(data)
        
        return data[user_key]
    
    def create_default_user(self, user_id: int) -> Dict[str, Any]:
        """Создает пользователя по умолчанию"""
        now = datetime.now()
        return {
            "user_id": user_id,
            "username": None,
            "first_name": None,
            "last_name": None,
            "registration_date": now.isoformat(),
            "last_activity": now.isoformat(),
            "daily_messages": 0,
            "last_message_date": now.strftime("%Y-%m-%d"),
            "ai_role": "cortex",  # Роль AI по умолчанию
            "subscription": {
                "type": "free",
                "expires_at": None,
                "unlimited": False
            },
            "statistics": {
                "total_messages": 0,
                "ai_requests": 0,
                "total_sessions": 0
            },
            "chat_history": []
        }
    
    def update_user_info(self, user_id: int, username: str = None, 
                        first_name: str = None, last_name: str = None) -> bool:
        """Обновляет информацию о пользователе"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        if username:
            user["username"] = username
        if first_name:
            user["first_name"] = first_name
        if last_name:
            user["last_name"] = last_name
        
        user["last_activity"] = datetime.now().isoformat()
        data[user_key] = user
        
        return self.save_data(data)
    
    def can_send_message(self, user_id: int) -> bool:
        """Проверяет может ли пользователь отправить сообщение"""
        user = self.get_user(user_id)
        
        # Если есть активная подписка
        if user["subscription"]["type"] != "free":
            if user["subscription"]["unlimited"]:
                return True
            
            expires_at = datetime.fromisoformat(user["subscription"]["expires_at"])
            if datetime.now() < expires_at:
                return True
            else:
                # Подписка истекла
                self.reset_subscription(user_id)
        
        # Проверяем дневной лимит для бесплатных пользователей
        today = datetime.now().strftime("%Y-%m-%d")
        if user["last_message_date"] != today:
            # Новый день - сбрасываем счетчик
            self.reset_daily_messages(user_id)
            return True
        
        return user["daily_messages"] < DAILY_FREE_MESSAGES
    
    def increment_message_count(self, user_id: int) -> bool:
        """Увеличивает счетчик сообщений"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        today = datetime.now().strftime("%Y-%m-%d")
        if user["last_message_date"] != today:
            user["daily_messages"] = 0
            user["last_message_date"] = today
        
        user["daily_messages"] += 1
        user["statistics"]["total_messages"] += 1
        user["statistics"]["ai_requests"] += 1
        user["last_activity"] = datetime.now().isoformat()
        
        data[user_key] = user
        return self.save_data(data)
    
    def reset_daily_messages(self, user_id: int) -> bool:
        """Сбрасывает дневной счетчик сообщений"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        user["daily_messages"] = 0
        user["last_message_date"] = datetime.now().strftime("%Y-%m-%d")
        
        data[user_key] = user
        return self.save_data(data)
    
    def reset_subscription(self, user_id: int) -> bool:
        """Сбрасывает подписку на бесплатную"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        user["subscription"] = {
            "type": "free",
            "expires_at": None,
            "unlimited": False
        }
        
        data[user_key] = user
        return self.save_data(data)
    
    def grant_subscription(self, user_id: int, plan_key: str) -> bool:
        """Выдает подписку пользователю"""
        if plan_key not in SUBSCRIPTION_PLANS:
            return False
        
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        plan = SUBSCRIPTION_PLANS[plan_key]
        
        if plan['duration_days'] == -1:  # Навсегда
            user["subscription"] = {
                "type": plan_key,
                "expires_at": None,
                "unlimited": True
            }
        else:
            expires_at = datetime.now() + timedelta(days=plan['duration_days'])
            user["subscription"] = {
                "type": plan_key,
                "expires_at": expires_at.isoformat(),
                "unlimited": False
            }
        
        data[user_key] = user
        return self.save_data(data)
    
    def revoke_subscription(self, user_id: int) -> bool:
        """Отзывает подписку у пользователя"""
        data = self.load_data()
        user_key = str(user_id)
        
        if user_key not in data:
            return False
        
        user = data[user_key]
        user["subscription"] = {
            "type": "free",
            "expires_at": None,
            "unlimited": False
        }
        
        data[user_key] = user
        return self.save_data(data)
    
    def add_bonus_messages(self, user_id: int, bonus_count: int = 10) -> bool:
        """Добавляет бонусные сообщения пользователю"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        # Добавляем бонусные сообщения (максимум до 50 в день)
        current_messages = user.get('daily_messages', 0)
        max_daily = DAILY_FREE_MESSAGES + 40  # 20 обычных + 40 бонусных максимум
        
        if current_messages >= max_daily:
            return False  # Уже максимум
        
        # Вычисляем сколько можно добавить
        available_to_add = max_daily - current_messages
        actual_bonus = min(bonus_count, available_to_add)
        
        # Уменьшаем счетчик сообщений (эффективно добавляем бесплатные)
        user['daily_messages'] = max(0, current_messages - actual_bonus)
        
        data[user_key] = user
        return self.save_data(data) and actual_bonus > 0
    
    def grant_bonus_to_all_users(self, bonus_count: int = 10) -> int:
        """Начисляет бонусные сообщения всем пользователям"""
        data = self.load_data()
        success_count = 0
        
        for user_id_str in data.keys():
            user_id = int(user_id_str)
            if self.add_bonus_messages(user_id, bonus_count):
                success_count += 1
        
        return success_count
    
    def add_to_history(self, user_id: int, role: str, content: str) -> bool:
        """Добавляет сообщение в историю пользователя"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        user["chat_history"].append(message)
        
        # Ограничиваем историю последними 100 сообщениями
        if len(user["chat_history"]) > 100:
            user["chat_history"] = user["chat_history"][-100:]
        
        data[user_key] = user
        return self.save_data(data)
    
    def get_history_for_ai(self, user_id: int, limit: int = 20) -> List[Dict[str, str]]:
        """Получает историю для AI API"""
        user = self.get_user(user_id)
        history = user.get("chat_history", [])
        
        recent_history = history[-limit:] if len(history) > limit else history
        
        ai_history = []
        for msg in recent_history:
            ai_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return ai_history
    
    def clear_history(self, user_id: int) -> bool:
        """Очищает историю пользователя"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        user["chat_history"] = []
        data[user_key] = user
        
        return self.save_data(data)
    
    def set_ai_role(self, user_id: int, role: str) -> bool:
        """Устанавливает роль AI для пользователя"""
        if role not in AI_ROLES:
            return False
            
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        user["ai_role"] = role
        user["last_activity"] = datetime.now().isoformat()
        data[user_key] = user
        
        return self.save_data(data)
    
    def get_ai_role(self, user_id: int) -> str:
        """Получает текущую роль AI пользователя"""
        user = self.get_user(user_id)
        return user.get("ai_role", "cortex")
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя"""
        user = self.get_user(user_id)
        
        subscription_info = "🆓 Бесплатная"
        daily_usage = f"{user['daily_messages']}/{DAILY_FREE_MESSAGES}"
        
        if user["subscription"]["type"] != "free":
            plan = SUBSCRIPTION_PLANS.get(user["subscription"]["type"], {})
            if user["subscription"]["unlimited"]:
                subscription_info = f"♾️ {plan.get('name', 'Неизвестная')} (Навсегда)"
                daily_usage = "♾️ Безлимитно"
            else:
                expires_at = datetime.fromisoformat(user["subscription"]["expires_at"])
                if datetime.now() < expires_at:
                    days_left = (expires_at - datetime.now()).days
                    subscription_info = f"💎 {plan.get('name', 'Неизвестная')} (осталось {days_left} дней)"
                    daily_usage = "♾️ Безлимитно"
                else:
                    subscription_info = "🆓 Бесплатная (истекла)"
                    daily_usage = f"{user['daily_messages']}/{DAILY_FREE_MESSAGES}"
        
        return {
            "user_info": {
                "username": user.get("username", "Не указан"),
                "first_name": user.get("first_name", "Не указано"),
                "registration_date": datetime.fromisoformat(user["registration_date"]).strftime("%d.%m.%Y"),
            },
            "activity": {
                "total_messages": user["statistics"]["total_messages"],
                "ai_requests": user["statistics"]["ai_requests"],
                "daily_messages": daily_usage,
                "last_activity": datetime.fromisoformat(user["last_activity"]).strftime("%d.%m.%Y %H:%M")
            },
            "subscription": subscription_info
        }


class SubscriptionManager:
    """Управление платежами и подписками"""
    
    def __init__(self):
        self.payments_file = "pending_payments.json"
        self.ensure_payments_file()
    
    def ensure_payments_file(self):
        """Создает файл платежей если его нет"""
        if not os.path.exists(self.payments_file):
            self.save_payments({})
            logger.info(f"📁 Создан файл платежей: {self.payments_file}")
    
    def load_payments(self) -> Dict[str, Any]:
        """Загружает данные платежей"""
        try:
            with open(self.payments_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"❌ Ошибка загрузки платежей: {str(e)}")
            return {}
    
    def save_payments(self, data: Dict[str, Any]) -> bool:
        """Сохраняет данные платежей"""
        try:
            with open(self.payments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"❌ Ошибка сохранения платежей: {str(e)}")
            return False
    
    def create_payment(self, user_id: int, plan_key: str, file_id: str) -> str:
        """Создает новый платеж"""
        payments = self.load_payments()
        
        payment_id = f"pay_{user_id}_{int(time.time())}"
        
        payments[payment_id] = {
            "user_id": user_id,
            "plan_key": plan_key,
            "file_id": file_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "plan_info": SUBSCRIPTION_PLANS[plan_key]
        }
        
        self.save_payments(payments)
        return payment_id
    
    def approve_payment(self, payment_id: str) -> bool:
        """Одобряет платеж"""
        payments = self.load_payments()
        
        if payment_id not in payments:
            return False
        
        payment = payments[payment_id]
        payment["status"] = "approved"
        payment["approved_at"] = datetime.now().isoformat()
        
        self.save_payments(payments)
        return True
    
    def reject_payment(self, payment_id: str) -> bool:
        """Отклоняет платеж"""
        payments = self.load_payments()
        
        if payment_id not in payments:
            return False
        
        payment = payments[payment_id]
        payment["status"] = "rejected"
        payment["rejected_at"] = datetime.now().isoformat()
        
        self.save_payments(payments)
        return True
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о платеже"""
        payments = self.load_payments()
        return payments.get(payment_id)


# Initialize managers
ai_client = AIClient()
user_manager = UserManager()
subscription_manager = SubscriptionManager()

# Track users currently waiting for AI response
active_ai_requests = set()

# Track admin pending actions (for reason input)
admin_pending_actions = {}

# Technical maintenance mode
maintenance_mode = False


# Inline keyboards
def get_main_menu():
    """Главное меню"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💬 Чат с AI", callback_data="ai_chat"),
        telebot.types.InlineKeyboardButton("👤 Профиль", callback_data="profile")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        telebot.types.InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🎭 Роли AI", callback_data="ai_roles"),
        telebot.types.InlineKeyboardButton("💎 Подписки", callback_data="subscriptions")
    )
    return markup


def get_ai_roles_menu(current_role: str = "cortex"):
    """Меню выбора ролей AI"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for role_key, role_info in AI_ROLES.items():
        emoji = "✅" if role_key == current_role else "▫️"
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{emoji} {role_info['name']}", 
                callback_data=f"set_role_{role_key}"
            )
        )
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return markup


def get_subscription_menu():
    """Меню подписок"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for plan_key, plan_info in SUBSCRIPTION_PLANS.items():
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{plan_info['name']} - {plan_info['price']}", 
                callback_data=f"buy_{plan_key}"
            )
        )
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
    )
    return markup


def get_confirm_clear_menu():
    """Меню подтверждения очистки истории"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear"),
        telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="back_to_main")
    )
    return markup


def get_admin_payment_menu(payment_id: str):
    """Меню для админа при проверке платежа"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Выдать", callback_data=f"approve_{payment_id}"),
        telebot.types.InlineKeyboardButton("❌ Отказать", callback_data=f"reject_{payment_id}")
    )
    return markup


def get_back_menu():
    """Кнопка назад"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")
    )
    return markup


def get_admin_menu():
    """Админ панель с инлайн кнопками"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users_list"),
        telebot.types.InlineKeyboardButton("💎 Выдать подписку", callback_data="admin_grant_sub")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🚫 Забрать подписку", callback_data="admin_revoke_sub"),
        telebot.types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("💳 Платежи", callback_data="admin_payments")
    )
    
    # Кнопка технических работ
    maintenance_text = "🛠 Выключить тех. работы" if maintenance_mode else "⚙️ Включить тех. работы"
    markup.add(
        telebot.types.InlineKeyboardButton(maintenance_text, callback_data="admin_toggle_maintenance")
    )
    
    return markup


def get_admin_users_menu(users_data, page=0):
    """Меню выбора пользователя для выдачи подписки"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # Показываем по 8 пользователей на странице
    start_idx = page * 8
    end_idx = start_idx + 8
    users_list = list(users_data.items())[start_idx:end_idx]
    
    for user_id, user_data in users_list:
        name = user_data.get('first_name', 'Неизвестно')
        username = user_data.get('username', 'отсутствует')
        subscription = user_data.get('subscription', {}).get('type', 'free')
        sub_emoji = "🆓" if subscription == 'free' else "💎"
        
        button_text = f"{sub_emoji} {name} (@{username})"
        markup.add(
            telebot.types.InlineKeyboardButton(
                button_text, 
                callback_data=f"select_user_{user_id}"
            )
        )
    
    # Навигация по страницам
    nav_buttons = []
    total_pages = (len(users_data) + 7) // 8
    
    if page > 0:
        nav_buttons.append(
            telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data=f"users_page_{page-1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            telebot.types.InlineKeyboardButton("➡️ Далее", callback_data=f"users_page_{page+1}")
        )
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel")
    )
    
    return markup


def get_admin_users_with_subs_menu(users_data, page=0):
    """Меню выбора пользователя для отзыва подписки"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # Фильтруем только пользователей с подпиской
    users_with_subs = {k: v for k, v in users_data.items() 
                      if v.get('subscription', {}).get('type', 'free') != 'free'}
    
    if not users_with_subs:
        markup.add(
            telebot.types.InlineKeyboardButton("🚫 Нет пользователей с подписками", callback_data="none")
        )
    else:
        # Показываем по 8 пользователей на странице
        start_idx = page * 8
        end_idx = start_idx + 8
        users_list = list(users_with_subs.items())[start_idx:end_idx]
        
        for user_id, user_data in users_list:
            name = user_data.get('first_name', 'Неизвестно')
            username = user_data.get('username', 'отсутствует')
            subscription = user_data.get('subscription', {}).get('type', 'free')
            sub_plan = SUBSCRIPTION_PLANS.get(subscription, {}).get('name', subscription)
            
            button_text = f"💎 {name} (@{username}) - {sub_plan}"
            markup.add(
                telebot.types.InlineKeyboardButton(
                    button_text, 
                    callback_data=f"revoke_select_{user_id}"
                )
            )
        
        # Навигация по страницам
        nav_buttons = []
        total_pages = (len(users_with_subs) + 7) // 8
        
        if page > 0:
            nav_buttons.append(
                telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data=f"revoke_page_{page-1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                telebot.types.InlineKeyboardButton("➡️ Далее", callback_data=f"revoke_page_{page+1}")
            )
        
        if nav_buttons:
            markup.row(*nav_buttons)
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Админ панель", callback_data="admin_panel")
    )
    
    return markup


def get_subscription_plans_menu(user_id):
    """Меню выбора плана подписки для пользователя"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for plan_key, plan_info in SUBSCRIPTION_PLANS.items():
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{plan_info['name']} - {plan_info['price']}",
                callback_data=f"grant_plan_{user_id}_{plan_key}"
            )
        )
    
    markup.add(
        telebot.types.InlineKeyboardButton("🔙 Выбор пользователя", callback_data="admin_grant_sub")
    )
    
    return markup


def get_buy_subscription_menu():
    """Кнопка купить подписку"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💎 Приобрести подписку", callback_data="subscriptions")
    )
    return markup


# Bot handlers
@bot.message_handler(commands=['start'])
def start_handler(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Обновляем информацию о пользователе
    user_manager.update_user_info(user_id, username, first_name, last_name)
    
    welcome_text = f"""
🎆 <b>Добро пожаловать в CortexaAI!</b>

👋 Привет, <b>{first_name or 'друг'}</b>!


🎆 <b>МОИ ВОЗМОЖНОСТИ:</b>

💬 <b>Умное общение:</b> Llama-3.3-70B AI
🎭 <b>5 уникальных ролей:</b> От друга до эксперта
📚 <b>Полная история:</b> Все диалоги сохраняются
👤 <b>Персональный профиль:</b> Статистика и настройки


🎁 <b>БЕСПЛАТНО:</b>

✅ {DAILY_FREE_MESSAGES} сообщений каждые 24 часа
✅ Доступ ко всем ролям AI
✅ Полная статистика


💎 <b>ПРЕМИУМ ПОДПИСКА:</b>

♾️ Безлимитное общение
🚀 Приоритетная обработка
🎆 Поддержка 24/7


🔥 <b>НАЧНИТЕ ПРЯМО СЕЙЧАС!</b>
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='HTML', 
        reply_markup=get_main_menu()
    )
    
    logger.info(f"👋 Новый пользователь: {user_id} ({username})")


@bot.message_handler(commands=['admin'])
def admin_handler(message):
    """Обработчик админ команды"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")
        return
    
    users_count = len(user_manager.load_data())
    pending_payments = len([p for p in subscription_manager.load_payments().values() if p['status'] == 'pending'])
    
    maintenance_status = "⚙️ АКТИВНЫ" if maintenance_mode else "🛠 ОТКЛЮЧЕНЫ"
    
    admin_text = f"""
👑 <b>Админ панель</b>

📊 <b>Быстрая статистика:</b>
• Пользователей в системе: {users_count}
• Ожидающих платежей: {pending_payments}
• Технические работы: {maintenance_status}

🛠️ <b>Управление:</b>
• Используйте кнопки ниже для управления
• Платежи приходят автоматически

<i>Выберите действие:</i>
    """
    
    bot.send_message(message.chat.id, admin_text, parse_mode='HTML', reply_markup=get_admin_menu())


@bot.message_handler(commands=['stats'])
def stats_handler(message):
    """Обработчик команды /stats"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")
        return
    
    users_data = user_manager.load_data()
    pending_payments = len([p for p in subscription_manager.load_payments().values() if p['status'] == 'pending'])
    
    total_users = len(users_data)
    active_subscriptions = len([u for u in users_data.values() if u.get('subscription', {}).get('type') != 'free'])
    total_messages = sum(u.get('statistics', {}).get('total_messages', 0) for u in users_data.values())
    
    stats_text = f"""
📊 <b>Общая статистика бота</b>

👥 <b>Пользователи:</b>
• Всего: <b>{total_users}</b>
• С подпиской: <b>{active_subscriptions}</b>
• Бесплатных: <b>{total_users - active_subscriptions}</b>

💬 <b>Сообщения:</b>
• Всего отправлено: <b>{total_messages}</b>
• Активных запросов: <b>{len(active_ai_requests)}</b>

💳 <b>Платежи:</b>
• Ожидают проверки: <b>{pending_payments}</b>

<i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
    """
    
    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')


@bot.message_handler(commands=['users'])
def users_handler(message):
    """Обработчик команды /users"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")
        return
    
    users_data = user_manager.load_data()
    
    if not users_data:
        bot.send_message(message.chat.id, "👥 <b>Пользователей пока нет</b>", parse_mode='HTML')
        return
    
    users_text = "👥 <b>Список пользователей</b>\n\n"
    
    for user_id, user_data in list(users_data.items())[:10]:  # Показываем первых 10
        name = user_data.get('first_name', 'Неизвестно')
        username = user_data.get('username', 'отсутствует')
        subscription = user_data.get('subscription', {}).get('type', 'free')
        messages = user_data.get('statistics', {}).get('total_messages', 0)
        
        sub_emoji = "🆓" if subscription == 'free' else "💎"
        
        users_text += f"• <b>{name}</b> (@{username})\n"
        users_text += f"   ID: <code>{user_id}</code>\n"
        users_text += f"   {sub_emoji} {subscription} | 💬 {messages} сообщ.\n\n"
    
    if len(users_data) > 10:
        users_text += f"<i>... и еще {len(users_data) - 10} пользователей</i>"
    
    bot.send_message(message.chat.id, users_text, parse_mode='HTML')


@bot.message_handler(commands=['grant'])
def grant_handler(message):
    """Обработчик команды /grant"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")
        return
    
    try:
        # Парсим команду: /grant user_id plan
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(
                message.chat.id,
                "❌ <b>Неверный формат!</b>\n\nИспользуйте: <code>/grant user_id plan</code>\n\nПланы: 1month, 6months, 12months, lifetime",
                parse_mode='HTML'
            )
            return
        
        target_user_id = int(parts[1])
        plan_key = parts[2]
        
        if plan_key not in SUBSCRIPTION_PLANS:
            bot.send_message(
                message.chat.id,
                f"❌ <b>Неизвестный план!</b>\n\nДоступные: {', '.join(SUBSCRIPTION_PLANS.keys())}",
                parse_mode='HTML'
            )
            return
        
        # Выдаем подписку
        if user_manager.grant_subscription(target_user_id, plan_key):
            plan_info = SUBSCRIPTION_PLANS[plan_key]
            
            success_text = f"✅ <b>Подписка выдана!</b>\n\n"
            success_text += f"👤 Пользователь: <code>{target_user_id}</code>\n"
            success_text += f"💎 План: {plan_info['name']} ({plan_info['price']})\n"
            
            if plan_info['duration_days'] == -1:
                success_text += f"♾️ Длительность: Навсегда"
            else:
                expires_at = datetime.now() + timedelta(days=plan_info['duration_days'])
                success_text += f"📅 До: {expires_at.strftime('%d.%m.%Y')}"
            
            bot.send_message(message.chat.id, success_text, parse_mode='HTML')
            
            # Уведомляем пользователя
            try:
                bot.send_message(
                    target_user_id,
                    f"🎉 <b>Поздравляем!</b>\n\nВам выдана подписка: <b>{plan_info['name']}</b>\n\nТеперь вы можете общаться без ограничений! 🚀",
                    parse_mode='HTML'
                )
            except:
                pass  # Пользователь мог заблокировать бота
        else:
            bot.send_message(
                message.chat.id,
                "❌ <b>Ошибка при выдаче подписки!</b>",
                parse_mode='HTML'
            )
    
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ <b>Неверный ID пользователя!</b>\n\nID должен быть числом.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в /grant: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ <b>Произошла ошибка!</b>",
            parse_mode='HTML'
        )


@bot.message_handler(commands=['bonus'])
def bonus_handler(message):
    """Обработчик команды /bonus - начисление бонусов"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора!")
        return
    
    try:
        parts = message.text.split()
        bonus_count = 10  # По умолчанию
        
        if len(parts) > 1:
            bonus_count = int(parts[1])
        
        if bonus_count <= 0 or bonus_count > 50:
            bot.send_message(
                message.chat.id,
                "❌ <b>Неверное количество бонусов!</b>\n\nДопустимо: 1-50",
                parse_mode='HTML'
            )
            return
        
        success_count = user_manager.grant_bonus_to_all_users(bonus_count)
        
        bonus_text = f"""
🎁 <b>Бонусы начислены!</b>

💬 <b>Количество:</b> +{bonus_count} сообщений
👤 <b>Получили:</b> {success_count} пользователей

✅ <b>Операция завершена!</b>
        """
        
        bot.send_message(message.chat.id, bonus_text, parse_mode='HTML')
        logger.info(f"🎁 Админ {message.from_user.id} начислил +{bonus_count} бонусов {success_count} пользователям")
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ <b>Неверный формат!</b>\n\nИспользуйте: <code>/bonus [1-50]</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"❌ Ошибка в /bonus: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ <b>Произошла ошибка!</b>",
            parse_mode='HTML'
        )


@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    """Обработчик фотографий (скриншотов чеков)"""
    user_id = message.from_user.id
    
    photo_text = """
📸 <b>Скриншот получен!</b>

✅ Ваш скриншот оплаты отправлен администратору на проверку.

⏳ <b>Что дальше:</b>
• Администратор проверит ваш платеж
• Вы получите уведомление о результате
• При одобрении подписка активируется автоматически

🕐 <b>Время проверки:</b> до 24 часов

<i>Пожалуйста, ожидайте...</i>
    """
    
    bot.send_message(user_id, photo_text, parse_mode='HTML', reply_markup=get_back_menu())
    
    # Отправляем админу для проверки
    if ADMIN_ID:
        file_id = message.photo[-1].file_id
        
        # Создаем платеж (используем план "1month" по умолчанию)
        payment_id = subscription_manager.create_payment(user_id, "1month", file_id)
        
        user = user_manager.get_user(user_id)
        admin_text = f"""
💰 <b>Новый платеж на проверку</b>

👤 <b>Пользователь:</b>
• ID: <code>{user_id}</code>
• Имя: {user.get('first_name', 'Не указано')}
• Username: @{user.get('username', 'отсутствует')}

💎 <b>Подписка:</b> {SUBSCRIPTION_PLANS['1month']['name']} - {SUBSCRIPTION_PLANS['1month']['price']}

📸 <b>Скриншот оплаты:</b>
        """
        
        bot.send_photo(
            ADMIN_ID, 
            file_id, 
            caption=admin_text, 
            parse_mode='HTML',
            reply_markup=get_admin_payment_menu(payment_id)
        )
    
    logger.info(f"📸 Получен скриншот от пользователя {user_id}")


@bot.message_handler(func=lambda message: True)
def message_handler(message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Пропускаем команды - они обрабатываются отдельными хэндлерами
    if user_text and user_text.startswith('/'):
        return
    
    # Проверяем, админ ли ожидает ввод причины для отзыва подписки
    if user_id == ADMIN_ID and user_id in admin_pending_actions:
        pending_action = admin_pending_actions[user_id]
        
        if pending_action['action'] == 'waiting_revoke_reason':
            target_user_id = pending_action['target_user_id']
            message_id = pending_action['message_id']
            reason = user_text.strip()
            
            # Удаляем состояние ожидания
            del admin_pending_actions[user_id]
            
            # Отзываем подписку
            if user_manager.revoke_subscription(target_user_id):
                target_user = user_manager.get_user(target_user_id)
                
                # Успешно отозвали подписку
                success_text = f"""
✅ <b>Подписка отозвана!</b>

👤 <b>Пользователь:</b> {target_user.get('first_name', 'Неизвестно')}
🆔 <b>ID:</b> <code>{target_user_id}</code>
✏️ <b>Причина:</b> {reason}

💬 <b>Пользователь уведомлен</b>
                """
                
                bot.edit_message_text(
                    success_text, user_id, message_id, 
                    parse_mode='HTML', reply_markup=get_admin_menu()
                )
                
                # Уведомляем пользователя об отзыве подписки
                try:
                    bot.send_message(
                        target_user_id,
                        f"""
🚫 <b>Ваша подписка была отозвана</b>

👤 <b>Администратор отозвал вашу подписку</b>

✏️ <b>Причина:</b> {reason}

🎆 Теперь вы можете отправлять только {DAILY_FREE_MESSAGES} сообщений в день.

💸 Если хотите восстановить подписку, обратитесь к администратору.
                        """,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка уведомления пользователя: {str(e)}")
                    pass  # Пользователь мог заблокировать бота
            else:
                # Ошибка при отзыве подписки
                bot.edit_message_text(
                    "❌ <b>Ошибка при отзыве подписки!</b>", 
                    user_id, message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                )
            
            return
    
    # Проверяем, не ожидает ли пользователь уже ответа от AI
    if user_id in active_ai_requests:
        bot.send_message(
            user_id,
            "⏳ <b>Подождите!</b>\n\n🤖 Я еще обрабатываю ваш предыдущий запрос.\n\n<i>Пожалуйста, дождитесь ответа, а затем задавайте следующий вопрос.</i>",
            parse_mode='HTML'
        )
        return
    
    # Проверяем режим технических работ
    if maintenance_mode:
        maintenance_text = """
⚙️ <b>ТЕХНИЧЕСКИЕ РАБОТЫ</b> ⚙️

👋 Уважаемый пользователь!  

На данный момент в системе проходят <b>технические работы</b> 🛠  
Пожалуйста, попробуйте позже.  

💎 После завершения работ бот <b>автоматически</b> всем начислит  
🎁 +10 бесплатных запросов в качестве компенсации.  

Спасибо за понимание 🙏🚀
        """
        bot.send_message(user_id, maintenance_text, parse_mode='HTML', reply_markup=get_main_menu())
        return
    
    # Обновляем информацию о пользователе
    user_manager.update_user_info(
        user_id, 
        message.from_user.username, 
        message.from_user.first_name, 
        message.from_user.last_name
    )
    
    # Проверяем может ли пользователь отправить сообщение
    if not user_manager.can_send_message(user_id):
        user = user_manager.get_user(user_id)
        limit_text = f"""
⚡️ <b>ЛИМИТ СООБЩЕНИЙ НА СЕГОДНЯ ДОСТИГНУТ!</b> 

📊 <b>Ваша активность на сегодня:</b>
💬 Использовано: <b>{user['daily_messages']} из {DAILY_FREE_MESSAGES}</b> сообщений
🕐 Обновление лимита: <b>через 24 часа</b>
⏰ Следующий доступ: <b>завтра в это же время</b>

💎 <b>ПРЕМИУМ ПОДПИСКА - БЕЗЛИМИТНОЕ ОБЩЕНИЕ</b>

🔥 <b>Специальные цены:</b>
📅 <b>1 месяц</b> → <b>200₴</b>
📆 <b>6 месяцев</b> → <b>1000₴</b> <i>(-17%)</i>
🗓️ <b>12 месяцев</b> → <b>1800₴</b> <i>(-25%)</i>
♾️ <b>НАВСЕГДА</b> → <b>3999₴</b> <i>(-33%)</i>

🎆 <b>Преимущества премиум:</b>
✅ Безлимитное количество сообщений
✅ Приоритетная обработка запросов
✅ Доступ ко всем ролям AI
✅ Поддержка 24/7
✅ Расширенная статистика

🚀 <b>Возвращайтесь завтра или оформите подписку!</b>
        """
        
        bot.send_message(
            user_id, 
            limit_text, 
            parse_mode='HTML', 
            reply_markup=get_buy_subscription_menu()
        )
        return
    
    # Добавляем пользователя в список активных запросов
    active_ai_requests.add(user_id)
    
    # Увеличиваем счетчик сообщений
    user_manager.increment_message_count(user_id)
    
    # Добавляем сообщение пользователя в историю
    user_manager.add_to_history(user_id, "user", user_text)
    
    # Отправляем сообщение о начале обработки
    processing_msg = bot.send_message(
        user_id, 
        "🤖 Обрабатываю ваш запрос...", 
        parse_mode='HTML'
    )
    
    try:
        # Получаем историю для AI
        history = user_manager.get_history_for_ai(user_id)
        
        # Получаем роль AI пользователя
        user_role = user_manager.get_ai_role(user_id)
        
        # Отправляем запрос к AI
        ai_response = ai_client.chat_completion(history, user_role)
        
        if ai_response:
            # Добавляем ответ AI в историю
            user_manager.add_to_history(user_id, "assistant", ai_response)
            
            # Удаляем сообщение о обработке
            bot.delete_message(user_id, processing_msg.message_id)
            
            # Отправляем ответ от AI
            bot.send_message(
                user_id, 
                ai_response, 
                parse_mode='HTML', 
                reply_markup=get_back_menu()
            )
        else:
            # Ошибка AI
            bot.edit_message_text(
                "😔 Извините, произошла ошибка при обработке запроса. Попробуйте позже.",
                user_id,
                processing_msg.message_id,
                reply_markup=get_back_menu()
            )
    
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {str(e)}")
        bot.edit_message_text(
            "😔 Произошла ошибка. Попробуйте позже.",
            user_id,
            processing_msg.message_id,
            reply_markup=get_back_menu()
        )
    
    finally:
        # Убираем пользователя из списка активных запросов
        active_ai_requests.discard(user_id)
    
    logger.info(f"💬 Обработано сообщение от {user_id}: {user_text[:50]}...")


# Callback handlers
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик колбэков"""
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "back_to_main":
            welcome_text = f"""
🎆 <b>Добро пожаловать в CortexaAI!</b>

💎 <b>ВАШ ПЕРСОНАЛЬНЫЙ AI ПОМОЩНИК</b>

🚀 <b>Передовые возможности:</b>
🔹 <b>5 уникальных ролей AI</b> - от друга до эксперта
🔹 <b>Умное общение</b> - понимаю контекст
🔹 <b>Полная память</b> - помню всю историю
🔹 <b>Детальная статистика</b> - отслеживаю прогресс

🎯 <b>Выберите действие из меню:</b>

✨ <i>Готов помочь с любыми задачами!</i>
            """
            bot.edit_message_text(
                welcome_text,
                user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_main_menu()
            )
        elif data == "profile":
            stats = user_manager.get_user_stats(user_id)
            current_role = user_manager.get_ai_role(user_id)
            role_info = AI_ROLES.get(current_role, AI_ROLES['cortex'])
            
            profile_text = f"""
👤 <b>Профиль</b>

<b>Имя:</b> {stats['user_info']['first_name']}
<b>Username:</b> @{stats['user_info']['username']}
<b>Регистрация:</b> {stats['user_info']['registration_date']}

<b>Сообщений:</b> {stats['activity']['total_messages']}
<b>Сегодня:</b> {stats['activity']['daily_messages']}
<b>Подписка:</b> {stats['subscription']}

🎭 <b>Текущая роль AI:</b> {role_info['name']}
            """
            bot.edit_message_text(profile_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
        
        elif data == "stats":
            stats = user_manager.get_user_stats(user_id)
            current_role = user_manager.get_ai_role(user_id)
            role_info = AI_ROLES.get(current_role, AI_ROLES['cortex'])
            
            stats_text = f"""
📊 <b>Ваша статистика</b>

<b>👤 Активность:</b>
• Всего сообщений: <b>{stats['activity']['total_messages']}</b>
• AI запросов: <b>{stats['activity']['ai_requests']}</b>
• Сегодня использовано: <b>{stats['activity']['daily_messages']}</b>
• Последняя активность: <b>{stats['activity']['last_activity']}</b>

<b>💎 Подписка:</b>
• Статус: {stats['subscription']}

<b>🎭 AI Роль:</b>
• Активна: {role_info['name']}

<b>🤖 Система:</b>
• AI Модель: <b>Llama-3.3-70B-Instruct</b>
• API: <b>Intelligence.io</b>
• Статус: <b>🟢 Онлайн</b>

<i>Обновлено: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}</i>
            """
            bot.edit_message_text(stats_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
        
        elif data == "ai_chat":
            current_role = user_manager.get_ai_role(user_id)
            role_info = AI_ROLES.get(current_role, AI_ROLES['cortex'])
            
            chat_text = f"""
💬 <b>Чат с Cortexa активирован!</b>

🎭 <b>Активная роль:</b> {role_info['name']}
📝 <b>Описание:</b> {role_info['description']}

🤖 Напишите мне любой вопрос или сообщение, и я отвечу в соответствии с выбранной ролью!

📚 История нашего общения сохраняется автоматически.

<b>Примеры вопросов:</b>
• "Расскажи анекдот"
• "Как приготовить борщ?"
• "Объясни квантовую физику"
• "Придумай стихотворение"
• "Помоги с домашним заданием"

✨ <i>Просто напишите сообщение!</i>
            """
            bot.edit_message_text(chat_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
        
        elif data == "ai_roles":
            current_role = user_manager.get_ai_role(user_id)
            current_role_info = AI_ROLES.get(current_role, AI_ROLES['cortex'])
            
            roles_text = f"""
🎭 <b>Выбор роли AI</b>

🎆 <b>Текущая роль:</b> {current_role_info['name']}
📝 <b>Описание:</b> {current_role_info['description']}

🔄 <b>Доступные роли:</b>
            """
            
            for role_key, role_info in AI_ROLES.items():
                status = "🟢" if role_key == current_role else ""
                roles_text += f"\n• {role_info['name']} - {role_info['description']} {status}"
            
            roles_text += "\n\n👉 <i>Выберите роль ниже:</i>"
            
            bot.edit_message_text(roles_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_ai_roles_menu(current_role))
        
        elif data.startswith("set_role_"):
            new_role = data.replace("set_role_", "")
            if user_manager.set_ai_role(user_id, new_role):
                role_info = AI_ROLES[new_role]
                
                # Очищаем историю при смене роли
                user_manager.clear_history(user_id)
                
                success_text = f"""
🎉 <b>Роль сменена!</b>

🎆 <b>НОВАЯ ЛИЧНОСТЬ АКТИВНА:</b>

🎭 <b>Роль:</b> {role_info['name']}
📝 <b>Описание:</b> {role_info['description']}

🗑️ <b>История чата очищена для новой роли</b>

🚀 <b>Теперь можно общаться с новой личностью!</b>
                """
                bot.edit_message_text(success_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
            else:
                bot.edit_message_text(
                    "❌ <b>Ошибка при смене роли!</b>", 
                    user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu()
                )
        
        elif data == "clear_history":
            confirm_text = "🗑️ <b>Очистить историю?</b>\n\n⚠️ Это действие нельзя отменить!\n\n📚 Будет удалена вся история ваших диалогов с AI."
            bot.edit_message_text(confirm_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_confirm_clear_menu())
        
        elif data == "confirm_clear":
            if user_manager.clear_history(user_id):
                success_text = "✅ <b>История очищена!</b>"
            else:
                success_text = "❌ Ошибка при очистке."
            bot.edit_message_text(success_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
        
        elif data == "subscriptions":
            subs_text = f"""
💎 <b>Подписки</b>

🎁 <b>Преимущества:</b>
• Безлимитное общение
• Приоритетная обработка
• Поддержка 24/7

💳 <b>Оплата:</b> Перевод + скриншот
            """
            bot.edit_message_text(subs_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_subscription_menu())
        
        elif data.startswith("buy_"):
            plan_key = data.replace("buy_", "")
            if plan_key in SUBSCRIPTION_PLANS:
                plan = SUBSCRIPTION_PLANS[plan_key]
                payment_text = f"""
💳 <b>Оплата: {plan['name']}</b>

💰 <b>Стоимость:</b> {plan['price']}

🏦 <b>Реквизиты:</b>
💳 Карта: <code>5536 9138 0000 0000</code>
🏦 Сбербанк

📸 <b>После оплаты:</b>
1. Сделайте скриншот чека
2. Отправьте фото сюда
3. Ожидайте подтверждения

<i>Отправьте скриншот фотографией в чат</i>
                """
                bot.edit_message_text(payment_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_back_menu())
        
        elif data.startswith("approve_"):
            if user_id != ADMIN_ID:
                return
            payment_id = data.replace("approve_", "")
            payment = subscription_manager.get_payment(payment_id)
            if payment and subscription_manager.approve_payment(payment_id):
                user_manager.grant_subscription(payment["user_id"], payment["plan_key"])
                bot.edit_message_caption(
                    f"✅ <b>Платеж одобрен!</b>\n\nПодписка выдана пользователю.",
                    user_id, call.message.message_id, parse_mode='HTML'
                )
                bot.send_message(
                    payment["user_id"],
                    f"✅ <b>Подписка активирована!</b>\n\n💎 {payment['plan_info']['name']} успешно подключена.\nМожете общаться без ограничений!",
                    parse_mode='HTML', reply_markup=get_main_menu()
                )
        
        elif data.startswith("reject_"):
            if user_id != ADMIN_ID:
                return
            payment_id = data.replace("reject_", "")
            payment = subscription_manager.get_payment(payment_id)
            if payment and subscription_manager.reject_payment(payment_id):
                bot.edit_message_caption(
                    f"❌ <b>Платеж отклонен</b>\n\nПользователь уведомлен.",
                    user_id, call.message.message_id, parse_mode='HTML'
                )
                bot.send_message(
                    payment["user_id"],
                    f"❌ <b>Платеж отклонен</b>\n\nК сожалению, ваш платеж не может быть подтвержден.\nПопробуйте еще раз или обратитесь в поддержку.",
                    parse_mode='HTML', reply_markup=get_main_menu()
                )
        
        # Новые обработчики для админ панели
        elif data == "admin_panel":
            if user_id != ADMIN_ID:
                return
            users_count = len(user_manager.load_data())
            pending_payments = len([p for p in subscription_manager.load_payments().values() if p['status'] == 'pending'])
            
            admin_text = f"""
👑 <b>Админ панель</b>

📊 <b>Быстрая статистика:</b>
• Пользователей в системе: {users_count}
• Ожидающих платежей: {pending_payments}

🛠️ <b>Управление:</b>
• Используйте кнопки ниже для управления
• Платежи приходят автоматически

<i>Выберите действие:</i>
            """
            bot.edit_message_text(admin_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu())
        
        elif data == "admin_users_list":
            if user_id != ADMIN_ID:
                return
            users_data = user_manager.load_data()
            if not users_data:
                bot.edit_message_text(
                    "👥 <b>Пользователей пока нет</b>", 
                    user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                )
                return
            
            users_text = f"👥 <b>Список пользователей ({len(users_data)})</b>\n\nВыберите пользователя для просмотра:"
            bot.edit_message_text(
                users_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_admin_users_menu(users_data)
            )
        
        elif data == "admin_grant_sub":
            if user_id != ADMIN_ID:
                return
            users_data = user_manager.load_data()
            if not users_data:
                bot.edit_message_text(
                    "👥 <b>Нет пользователей для выдачи подписки</b>", 
                    user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                )
                return
            
            grant_text = f"💎 <b>Выдача подписки</b>\n\n👥 Всего пользователей: {len(users_data)}\n\nВыберите пользователя:"
            bot.edit_message_text(
                grant_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_admin_users_menu(users_data)
            )
        
        elif data == "admin_revoke_sub":
            if user_id != ADMIN_ID:
                return
            users_data = user_manager.load_data()
            if not users_data:
                bot.edit_message_text(
                    "👥 <b>Нет пользователей для отзыва подписки</b>", 
                    user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                )
                return
            
            revoke_text = f"🚫 <b>Отзыв подписок</b>\n\n👥 Всего пользователей: {len(users_data)}\n\nВыберите пользователя для отзыва подписки:"
            bot.edit_message_text(
                revoke_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_admin_users_with_subs_menu(users_data)
            )
        
        elif data == "admin_stats":
            if user_id != ADMIN_ID:
                return
            users_data = user_manager.load_data()
            pending_payments = len([p for p in subscription_manager.load_payments().values() if p['status'] == 'pending'])
            
            total_users = len(users_data)
            active_subscriptions = len([u for u in users_data.values() if u.get('subscription', {}).get('type') != 'free'])
            total_messages = sum(u.get('statistics', {}).get('total_messages', 0) for u in users_data.values())
            
            stats_text = f"""
📊 <b>Общая статистика бота</b>

👥 <b>Пользователи:</b>
• Всего: <b>{total_users}</b>
• С подпиской: <b>{active_subscriptions}</b>
• Бесплатных: <b>{total_users - active_subscriptions}</b>

💬 <b>Сообщения:</b>
• Всего отправлено: <b>{total_messages}</b>
• Активных запросов: <b>{len(active_ai_requests)}</b>

💳 <b>Платежи:</b>
• Ожидают проверки: <b>{pending_payments}</b>

<i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
            """
            bot.edit_message_text(stats_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu())
        
        elif data == "admin_payments":
            if user_id != ADMIN_ID:
                return
            payments = subscription_manager.load_payments()
            pending = [p for p in payments.values() if p['status'] == 'pending']
            
            if not pending:
                payments_text = "💳 <b>Платежи</b>\n\n✅ Нет ожидающих платежей"
            else:
                payments_text = f"💳 <b>Платежи ({len(pending)} ожидают)</b>\n\n"
                for payment in pending[:5]:  # Показываем только первые 5
                    user_data = user_manager.get_user(payment['user_id'])
                    name = user_data.get('first_name', 'Неизвестно')
                    payments_text += f"• {name} - {payment['plan_info']['name']}\n"
                if len(pending) > 5:
                    payments_text += f"\n<i>... и еще {len(pending) - 5} платежей</i>"
            
            bot.edit_message_text(payments_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu())
        
        elif data == "admin_toggle_maintenance":
            if user_id != ADMIN_ID:
                return
            
            global maintenance_mode
            was_maintenance = maintenance_mode
            maintenance_mode = not maintenance_mode
            
            status_text = "включен" if maintenance_mode else "выключен"
            emoji = "⚙️" if maintenance_mode else "🛠"
            
            # Если выключаем режим тех. работ - начисляем бонусы
            bonus_users = 0
            if was_maintenance and not maintenance_mode:
                bonus_users = user_manager.grant_bonus_to_all_users(10)
                logger.info(f"🎁 Начислено +10 бонусных запросов {bonus_users} пользователям")
            
            maintenance_text = f"""
{emoji} <b>Режим технических работ {status_text}</b>

🔄 <b>Статус:</b> {'ACTIVE' if maintenance_mode else 'DISABLED'}

💬 <b>Описание:</b>
• {'AI запросы заблокированы' if maintenance_mode else 'AI запросы разрешены'}
• Пользователи могут менять роли и настройки
• После выключения +10 бонусных запросов
            """
            
            if bonus_users > 0:
                maintenance_text += f"\n🎁 <b>Бонусы начислены {bonus_users} пользователям!</b>"
            
            bot.edit_message_text(maintenance_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu())
            
            logger.info(f"🔧 Админ {user_id} {status_text} режим технических работ")
        
        elif data.startswith("users_page_"):
            if user_id != ADMIN_ID:
                return
            page = int(data.replace("users_page_", ""))
            users_data = user_manager.load_data()
            users_text = f"👥 <b>Список пользователей ({len(users_data)})</b>\n\nВыберите пользователя для просмотра:"
            bot.edit_message_text(
                users_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_admin_users_menu(users_data, page)
            )
        
        elif data.startswith("revoke_page_"):
            if user_id != ADMIN_ID:
                return
            page = int(data.replace("revoke_page_", ""))
            users_data = user_manager.load_data()
            revoke_text = f"🚫 <b>Отзыв подписок</b>\n\n👥 Всего пользователей: {len(users_data)}\n\nВыберите пользователя для отзыва подписки:"
            bot.edit_message_text(
                revoke_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_admin_users_with_subs_menu(users_data, page)
            )
        
        elif data.startswith("select_user_"):
            if user_id != ADMIN_ID:
                return
            target_user_id = int(data.replace("select_user_", ""))
            target_user = user_manager.get_user(target_user_id)
            
            # Показываем информацию о пользователе и предлагаем выбрать план
            user_info_text = f"""
👤 <b>Информация о пользователе</b>

<b>Имя:</b> {target_user.get('first_name', 'Не указано')}
<b>Username:</b> @{target_user.get('username', 'отсутствует')}
<b>ID:</b> <code>{target_user_id}</code>
<b>Регистрация:</b> {datetime.fromisoformat(target_user['registration_date']).strftime('%d.%m.%Y')}

<b>Текущая подписка:</b> {target_user.get('subscription', {}).get('type', 'free')}
<b>Сообщений:</b> {target_user.get('statistics', {}).get('total_messages', 0)}

💎 <b>Выберите план подписки:</b>
            """
            bot.edit_message_text(
                user_info_text, user_id, call.message.message_id, 
                parse_mode='HTML', reply_markup=get_subscription_plans_menu(target_user_id)
            )
        
        elif data.startswith("grant_plan_"):
            if user_id != ADMIN_ID:
                return
            parts = data.replace("grant_plan_", "").split("_")
            target_user_id = int(parts[0])
            plan_key = "_".join(parts[1:])
            
            if plan_key in SUBSCRIPTION_PLANS:
                if user_manager.grant_subscription(target_user_id, plan_key):
                    plan_info = SUBSCRIPTION_PLANS[plan_key]
                    target_user = user_manager.get_user(target_user_id)
                    
                    success_text = f"""
✅ <b>Подписка выдана!</b>

👤 <b>Пользователь:</b> {target_user.get('first_name', 'Неизвестно')}
🆔 <b>ID:</b> <code>{target_user_id}</code>
💎 <b>План:</b> {plan_info['name']} ({plan_info['price']})

                    """
                    if plan_info['duration_days'] == -1:
                        success_text += "♾️ <b>Длительность:</b> Навсегда"
                    else:
                        expires_at = datetime.now() + timedelta(days=plan_info['duration_days'])
                        success_text += f"📅 <b>До:</b> {expires_at.strftime('%d.%m.%Y')}"
                    
                    bot.edit_message_text(success_text, user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu())
                    
                    # Уведомляем пользователя
                    try:
                        bot.send_message(
                            target_user_id,
                            f"🎉 <b>Поздравляем!</b>\n\nВам выдана подписка: <b>{plan_info['name']}</b>\n\nТеперь вы можете общаться без ограничений! 🚀",
                            parse_mode='HTML'
                        )
                    except:
                        pass  # Пользователь мог заблокировать бота
                else:
                    bot.edit_message_text(
                        "❌ <b>Ошибка при выдаче подписки!</b>", 
                        user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                    )
            else:
                bot.edit_message_text(
                    "❌ <b>Неизвестный план подписки!</b>", 
                    user_id, call.message.message_id, parse_mode='HTML', reply_markup=get_admin_menu()
                )
        
        elif data.startswith("revoke_select_"):
            if user_id != ADMIN_ID:
                return
            target_user_id = int(data.replace("revoke_select_", ""))
            target_user = user_manager.get_user(target_user_id)
            
            # Показываем информацию о пользователе и просим ввести причину
            user_info_text = f"""
🚫 <b>Отзыв подписки</b>

👤 <b>Пользователь:</b> {target_user.get('first_name', 'Не указано')}
📱 <b>Username:</b> @{target_user.get('username', 'отсутствует')}
🆔 <b>ID:</b> <code>{target_user_id}</code>

💎 <b>Текущая подписка:</b> {target_user.get('subscription', {}).get('type', 'free')}
💬 <b>Сообщений:</b> {target_user.get('statistics', {}).get('total_messages', 0)}

✏️ <b>Напишите причину отзыва подписки:</b>

<i>Пользователь увидит эту причину в уведомлении</i>
            """
            
            # Сохраняем состояние ожидания ввода причины
            admin_pending_actions[user_id] = {
                'action': 'waiting_revoke_reason',
                'target_user_id': target_user_id,
                'message_id': call.message.message_id
            }
            
            bot.edit_message_text(
                user_info_text, user_id, call.message.message_id, 
                parse_mode='HTML'
            )
        
        bot.answer_callback_query(call.id)
    
    except Exception as e:
        logger.error(f"❌ Ошибка обработки callback: {str(e)}")
        bot.answer_callback_query(call.id, "Ошибка обработки")


# Flask webhook setup
@app.route('/', methods=['GET'])
def index():
    return "<h1>AI Telegram Bot</h1><p>Bot is running!</p>"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Error', 403


def set_webhook():
    """Set up webhook for Railway deployment"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
    else:
        logger.warning("⚠️ WEBHOOK_URL not set, running in polling mode")


if __name__ == '__main__':
    logger.info("🚀 Starting AI Telegram Bot...")
    
    # Test AI connection
    if ai_client.chat_completion([{"role": "user", "content": "Test"}]):
        logger.info("✅ AI connection successful")
    else:
        logger.error("❌ AI connection failed")
    
    if WEBHOOK_URL:
        # Production mode with webhook
        set_webhook()
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        # Development mode with polling
        logger.info("🔄 Starting polling mode...")
        bot.infinity_polling()
    
    def reset_subscription(self, user_id: int) -> bool:
        """Сбрасывает статус подписки"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        user["subscription"] = {
            "type": "free",
            "expires_at": None,
            "unlimited": False
        }
        
        data[user_key] = user
        return self.save_data(data)

    def upgrade_subscription(self, user_id: int, subscription_type: str) -> bool:
        """Обновляет статус подписки"""
        data = self.load_data()
        user_key = str(user_id)
        user = data.get(user_key, self.create_default_user(user_id))
        
        if subscription_type not in SUBSCRIPTION_PLANS:
            logger.error(f"❌ Неизвестный тип подписки: {subscription_type}")
            return False
        
        plan = SUBSCRIPTION_PLANS[subscription_type]
        
        if plan['duration_days'] == -1:
            user["subscription"] = {
                "type": subscription_type,
                "expires_at": None,
                "unlimited": True
            }
        else:
            expires_at = datetime.now() + timedelta(days=plan['duration_days'])
            user["subscription"] = {
                "type": subscription_type,
                "expires_at": expires_at.isoformat(),
                "unlimited": False
            }
        
        data[user_key] = user
        return self.save_data(data)

    def generate_subscription_url(self, user_id: int, subscription_type: str) -> str:
        """Генерирует ссылку для оплаты подписки"""
        if subscription_type not in SUBSCRIPTION_PLANS:
            logger.error(f"❌ Неизвестный тип подписки: {subscription_type}")
            return "Ссылка для оплаты недоступна."
        
        plan = SUBSCRIPTION_PLANS[subscription_type]
        
        # Здесь должна быть логика для генерации ссылки оплаты
        # Например, создание платежного запроса и получение URL
        
        return "https://example.com/pay"


def create_main_menu():
    """Создает главное меню с красивыми inline кнопками"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        [types.InlineKeyboardButton("💬 Новый чат", callback_data="new_chat"),
         types.InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         types.InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history_confirm")],
        [types.InlineKeyboardButton("ℹ️ О боте", callback_data="about"),
         types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    
    for row in buttons:
        keyboard.row(*row)
    
    return keyboard

def create_chat_menu():
    """Создает меню для режима чата"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        [types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
         types.InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [types.InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history_confirm"),
         types.InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    
    for row in buttons:
        keyboard.row(*row)
    
    return keyboard

def create_confirmation_menu(action_data: str):
    """Создает меню подтверждения действия"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("✅ Да, подтвердить", callback_data=f"confirm_{action_data}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="main_menu")
    ]
    
    keyboard.row(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        # Обновляем информацию о пользователе
        user_profile.update_user_info(user_id, username, first_name, last_name)
        
        # Загружаем историю чата
        history = chat_history.load_history(message.chat.id)
        
        welcome_text = f"""
🎉 <b>Добро пожаловать в AI Чат-Бот!</b> 🎉

👋 Привет, {first_name or 'друг'}!

🤖 Я ваш умный помощник на базе нейросети
✨ Готов ответить на любые вопросы
💬 Просто напишите мне что-нибудь!
📚 Помню нашу историю общения

{f"📖 У нас уже <b>{len(history)}</b> сообщений в истории" if history else "📝 Начинаем новую беседу"}

<i>Выберите действие из меню ниже:</i>
        """
        
        bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode='HTML',
            reply_markup=create_main_menu()
        )
        
        logger.info(f"Пользователь {user_id} ({username}) запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в send_welcome: {str(e)}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при запуске бота")

@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
    help_text = """
🆘 <b>Справка по использованию бота</b>

<b>Основные команды:</b>
• /start - Запуск бота
• /help - Эта справка
• /stats - Статистика использования

<b>Как пользоваться:</b>
1️⃣ Просто напишите мне любой вопрос
2️⃣ Я отвечу с помощью нейросети
3️⃣ Используйте inline кнопки для навигации
4️⃣ Вся история сохраняется автоматически

<b>Возможности AI:</b>
🧠 Ответы на вопросы
📝 Помощь с текстами
💡 Генерация идей
🔍 Поиск информации
📚 Обучение и объяснения
🗣️ Поддержание контекста беседы

<b>Управление:</b>
👤 Просмотр профиля и статистики
🗑️ Очистка истории с подтверждением
⚙️ Настройки бота

<i>Приятного общения! 😊</i>
    """
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='HTML',
        reply_markup=create_main_menu()
    )

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Обработчик команды /stats"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Получаем статистику пользователя
        user_stats = user_profile.get_user_stats(user_id)
        
        # Получаем статистику чата
        chat_stats = chat_history.get_chat_stats(chat_id)
        
        stats_text = f"""
📊 <b>Ваша статистика</b>

<b>👤 Профиль:</b>
• Всего сообщений: <b>{user_stats['activity']['total_messages']}</b>
• Запросов к AI: <b>{user_stats['activity']['ai_requests']}</b>
• Среднее в день: <b>{user_stats['activity']['avg_messages_per_day']}</b>
• За неделю: <b>{user_stats['activity']['week_messages']}</b>

<b>💬 Этот чат:</b>
• Сообщений в истории: <b>{chat_stats['total_messages']}</b>
• Ваших сообщений: <b>{chat_stats['user_messages']}</b>
• Ответов AI: <b>{chat_stats['ai_messages']}</b>

<b>🤖 Система:</b>
• Модель AI: <b>Llama-3.3-70B-Instruct</b>
• Статус: <b>🟢 Активен</b>
• Последняя активность: <b>{user_stats['activity']['last_activity']}</b>

<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>
        """
        
        bot.send_message(
            message.chat.id,
            stats_text,
            parse_mode='HTML',
            reply_markup=create_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в send_stats: {str(e)}")
        bot.send_message(message.chat.id, "❌ Ошибка получения статистики")

def handle_new_chat(chat_id: int, message_id: int):
    """Обработка кнопки 'Новый чат'"""
    history = chat_history.load_history(chat_id)
    
    chat_text = f"""
💬 <b>Режим AI чата активирован!</b>

🤖 Напишите мне любой вопрос или сообщение, и я отвечу с помощью нейросети.
📚 История нашего общения сохраняется автоматически

{f"📖 В нашей истории уже <b>{len(history)}</b> сообщений" if history else "📝 Начинаем новую беседу"}

<b>Примеры вопросов:</b>
• "Расскажи анекдот"
• "Как приготовить борщ?"
• "Объясни квантовую физику"
• "Придумай стихотворение"
• "Продолжи нашу беседу"

✨ <i>Жду ваших сообщений!</i>
    """
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=chat_text,
        parse_mode='HTML',
        reply_markup=create_chat_menu()
    )

def handle_profile(chat_id: int, message_id: int, user_id: int):
    """Обработка кнопки 'Профиль'"""
    profile_text = user_profile.format_profile_info(user_id)
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=profile_text,
        parse_mode='HTML',
        reply_markup=create_main_menu()
    )

def handle_clear_history_confirm(chat_id: int, message_id: int):
    """Обработка запроса на подтверждение очистки истории"""
    history = chat_history.load_history(chat_id)
    
    confirm_text = f"""
🗑️ <b>Подтверждение очистки истории</b>

⚠️ <b>Внимание!</b> Вы собираетесь удалить всю историю общения.

📊 <b>Что будет удалено:</b>
• Всего сообщений: <b>{len(history)}</b>
• Вся история диалогов с AI
• Контекст предыдущих бесед

💡 <b>Это действие нельзя отменить!</b>

Вы уверены, что хотите продолжить?
    """
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=confirm_text,
        parse_mode='HTML',
        reply_markup=create_confirmation_menu("clear_history")
    )

def handle_clear_history_execute(chat_id: int, message_id: int):
    """Выполнение очистки истории после подтверждения"""
    try:
        success = chat_history.clear_history(chat_id)
        
        if success:
            clear_text = """
✅ <b>История успешно очищена!</b>

🗑️ Все сообщения удалены
🆕 Начинаем с чистого листа
🤖 Готов к новым беседам!

<i>Что бы вы хотели обсудить?</i>
            """
        else:
            clear_text = """
❌ <b>Ошибка очистки истории</b>

Попробуйте еще раз или обратитесь к администратору.
            """
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=clear_text,
            parse_mode='HTML',
            reply_markup=create_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_clear_history_execute: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработчик callback запросов от inline кнопок"""
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # Сразу подтверждаем получение callback
        bot.answer_callback_query(call.id)
        
        if call.data == "new_chat":
            handle_new_chat(chat_id, message_id)
            
        elif call.data == "profile":
            handle_profile(chat_id, message_id, user_id)
            
        elif call.data == "stats":
            handle_stats_callback(chat_id, message_id, user_id)
            
        elif call.data == "clear_history_confirm":
            handle_clear_history_confirm(chat_id, message_id)
            
        elif call.data == "confirm_clear_history":
            handle_clear_history_execute(chat_id, message_id)
            
        elif call.data == "about":
            handle_about(chat_id, message_id)
            
        elif call.data == "settings":
            handle_settings(chat_id, message_id)
            
        elif call.data == "main_menu":
            handle_main_menu(chat_id, message_id)
            
        else:
            logger.warning(f"Неизвестный callback: {call.data}")
        
        logger.info(f"Пользователь {user_id} нажал кнопку: {call.data}")
        
    except Exception as e:
        logger.error(f"Ошибка в callback_query: {str(e)}")
        try:
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        except:
            pass

def handle_stats_callback(chat_id: int, message_id: int, user_id: int):
    """Обработка кнопки 'Статистика'"""
    try:
        user_stats = user_profile.get_user_stats(user_id)
        chat_stats = chat_history.get_chat_stats(chat_id)
        
        stats_text = f"""
📊 <b>Подробная статистика</b>

<b>👤 Ваш профиль:</b>
• Всего сообщений: <b>{user_stats['activity']['total_messages']}</b>
• Запросов к AI: <b>{user_stats['activity']['ai_requests']}</b>
• Среднее в день: <b>{user_stats['activity']['avg_messages_per_day']}</b>
• За неделю: <b>{user_stats['activity']['week_messages']}</b>

<b>💬 Этот чат:</b>
• Всего в истории: <b>{chat_stats['total_messages']}</b>
• Ваших сообщений: <b>{chat_stats['user_messages']}</b>
• Ответов AI: <b>{chat_stats['ai_messages']}</b>

<b>🤖 Система:</b>
• AI Модель: <b>Llama-3.3-70B-Instruct</b>
• API: <b>Intelligence.io</b>
• Статус: <b>🟢 Онлайн 24/7</b>

<i>Последнее обновление: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}</i>
        """
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=stats_text,
            parse_mode='HTML',
            reply_markup=create_main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_stats_callback: {str(e)}")

def handle_about(chat_id: int, message_id: int):
    """Обработка кнопки 'О боте'"""
    about_text = f"""
ℹ️ <b>О боте</b>

🤖 <b>AI Чат-Бот</b> - современный помощник на базе нейросети

<b>Технологии:</b>
• 🧠 Llama-3.3-70B-Instruct
• 🐍 Python + pyTelegramBotAPI
• ☁️ Intelligence.io API
• 🚀 Деплой на Railway
• 📚 Система истории чатов
• 👤 Персональные профили

<b>Разработчик:</b>
• 👨‍💻 Создан с любовью к AI
• 🎯 Цель: Сделать AI доступным всем
• 📧 Обратная связь через бота

<b>Версия:</b> 2.0.0
<b>Дата релиза:</b> 31.08.2025

<i>Спасибо за использование! 💙</i>
    """
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=about_text,
        parse_mode='HTML',
        reply_markup=create_main_menu()
    )

def handle_settings(chat_id: int, message_id: int):
    """Обработка кнопки 'Настройки'"""
    settings_text = """
⚙️ <b>Настройки бота</b>

<b>Текущие настройки:</b>
• 🌡️ Температура AI: <b>0.7</b>
• 📏 Макс. токенов: <b>500к</b>
• ⏱️ Таймаут: <b>30 сек</b>
• 🔄 Авто-сохранение: <b>Вкл</b>
• 📚 История чатов: <b>Вкл</b>

<b>Языковые настройки:</b>
• 🗣️ Язык ответов: <b>Русский</b>
• 🌍 Регион: <b>RU</b>

<b>Конфиденциальность:</b>
• 🔐 Локальное хранение истории
• 🛡️ Защищенные профили
• 🚫 Без отслеживания

<i>Настройки оптимизированы для лучшей работы</i>

💡 <b>Совет:</b> Задавайте конкретные вопросы для лучших ответов!
    """
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=settings_text,
        parse_mode='HTML',
        reply_markup=create_main_menu()
    )

def handle_main_menu(chat_id: int, message_id: int):
    """Обработка кнопки 'Главное меню'"""
    welcome_text = """
🏠 <b>Главное меню</b>

🤖 Добро пожаловать обратно!
Выберите действие из меню ниже:

✨ <i>Я всегда готов помочь!</i>
    """
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=welcome_text,
        parse_mode='HTML',
        reply_markup=create_main_menu()
    )

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Обработчик всех текстовых сообщений"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username
        user_message = message.text
        
        # Обновляем статистику пользователя
        user_profile.increment_message_count(user_id)
        user_profile.increment_ai_requests(user_id)
        
        # Показываем индикатор "печатает..."
        bot.send_chat_action(chat_id, 'typing')
        
        # Сохраняем сообщение пользователя в историю
        chat_history.add_message(chat_id, "user", user_message, username)
        
        # Получаем историю для контекста
        ai_history = chat_history.get_history_for_ai(chat_id, limit=20)
        
        # Получаем ответ от AI с учетом истории
        ai_response = ai_client.get_smart_response(user_message, ai_history)
        
        # Сохраняем ответ AI в историю
        chat_history.add_message(chat_id, "assistant", ai_response)
        
        # Добавляем красивое оформление к ответу
        formatted_response = f"""
{ai_response}

<i>💡 Есть еще вопросы? Просто напишите!</i>
        """
        
        # Отправляем ответ с меню
        bot.send_message(
            chat_id,
            formatted_response,
            parse_mode='HTML',
            reply_markup=create_chat_menu()
        )
        
        logger.info(f"Обработано сообщение от пользователя {user_id}: {user_message[:50]}...")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        
        error_text = """
❌ <b>Произошла ошибка</b>

🔧 Попробуйте:
• Отправить сообщение еще раз
• Использовать команду /start

<i>Извините за неудобства!</i>
        """
        
        bot.send_message(
            chat_id,
            error_text,
            parse_mode='HTML',
            reply_markup=create_main_menu()
        )

# Flask маршрут для webhook (для Railway деплоя)
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK"
    else:
        return "Bad Request", 400

@app.route('/')
def index():
    """Главная страница для проверки работоспособности"""
    try:
        total_users = len([f for f in os.listdir('profiles') if f.endswith('.json')]) if os.path.exists('profiles') else 0
        total_chats = len([f for f in os.listdir('history') if f.endswith('.json')]) if os.path.exists('history') else 0
    except:
        total_users = 0
        total_chats = 0
    
    return f"""
    <html>
        <head>
            <title>AI Telegram Bot</title>
            <style>
                body {{ font-family: Arial; text-align: center; margin: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .container {{ background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px); }}
                .status {{ color: #4CAF50; font-size: 24px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 AI Telegram Bot v2.0</h1>
                <p class="status">✅ Бот работает!</p>
                <p>🚀 Успешно развернут на Railway</p>
                <p>👥 Всего пользователей: {total_users}</p>
                <p>💬 Активных чатов: {total_chats}</p>
                <p>🧠 AI модель: Llama-4-Maverick-17B-128E</p>
                <p>📚 Система истории: Активна</p>
                <p><a href="https://t.me/YOUR_BOT_USERNAME" style="color: #FFD700;">🔗 Открыть бота в Telegram</a></p>
            </div>
        </body>
    </html>
    """

def set_webhook():
    """Устанавливает webhook для бота"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        bot.remove_webhook()
        time.sleep(1)
        result = bot.set_webhook(url=webhook_url)
        if result:
            logger.info(f"✅ Webhook установлен: {webhook_url}")
        else:
            logger.error("❌ Ошибка установки webhook")
    else:
        logger.info("⚠️ WEBHOOK_URL не задан, запуск в режиме polling")

def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск AI Telegram Bot v2.0...")
    logger.info(f"🤖 Модель AI: {ai_client.model}")
    logger.info(f"⚡ Порт: {PORT}")
    
    # Тестируем подключение к AI
    if ai_client.test_connection():
        logger.info("✅ AI API подключение успешно")
    else:
        logger.warning("⚠️ Проблемы с AI API")
    
    if WEBHOOK_URL:
        # Режим webhook для деплоя
        logger.info("🌐 Режим: Webhook (для продакшена)")
        set_webhook()
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        # Режим polling для локальной разработки
        logger.info("🏠 Режим: Polling (для разработки)")
        logger.info("✅ Бот запущен и готов к работе!")
        bot.polling(none_stop=True, interval=0, timeout=20)

if __name__ == '__main__':
    main()