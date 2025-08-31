"""
Утиліти для Telegram бота "Дніпро ОПЕРАТИВНИЙ"
"""

import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MessageCounter:
    """Клас для підрахунку повідомлень"""
    
    def __init__(self):
        self.total = 0
        self.today = 0
        self.last_reset = datetime.date.today()
    
    def increment(self):
        """Збільшити лічильники"""
        current_date = datetime.date.today()
        
        # Скинути денний лічильник при зміні дня
        if current_date != self.last_reset:
            self.today = 0
            self.last_reset = current_date
        
        self.total += 1
        self.today += 1
    
    def get_stats(self) -> dict:
        """Отримати статистику"""
        return {
            "total": self.total,
            "today": self.today,
            "date": self.last_reset.strftime("%Y-%m-%d")
        }


class UserTracker:
    """Клас для відстеження користувачів"""
    
    def __init__(self):
        self.users = set()
        self.active_today = set()
        self.last_reset = datetime.date.today()
    
    def add_user(self, user_id: int):
        """Додати користувача"""
        current_date = datetime.date.today()
        
        # Скинути денний список при зміні дня
        if current_date != self.last_reset:
            self.active_today.clear()
            self.last_reset = current_date
        
        self.users.add(user_id)
        self.active_today.add(user_id)
    
    def get_stats(self) -> dict:
        """Отримати статистику користувачів"""
        return {
            "total_users": len(self.users),
            "active_today": len(self.active_today),
            "date": self.last_reset.strftime("%Y-%m-%d")
        }


class MediaHandler:
    """Клас для обробки медіа файлів"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Форматувати розмір файлу"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_media_info(message) -> dict:
        """Отримати інформацію про медіа"""
        info = {
            "type": message.content_type,
            "caption": message.caption or "",
            "timestamp": message.date.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": message.from_user.id,
            "username": message.from_user.username or "Анонім"
        }
        
        if message.content_type == "photo":
            photo = message.photo[-1]  # Найвища якість
            info.update({
                "file_id": photo.file_id,
                "file_size": MediaHandler.format_file_size(photo.file_size or 0),
                "width": photo.width,
                "height": photo.height
            })
        
        elif message.content_type == "video":
            video = message.video
            info.update({
                "file_id": video.file_id,
                "file_size": MediaHandler.format_file_size(video.file_size or 0),
                "width": video.width,
                "height": video.height,
                "duration": f"{video.duration}s"
            })
        
        return info


class TextFormatter:
    """Клас для форматування тексту"""
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Екранувати HTML символи"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Обрізати текст до вказаної довжини"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def format_user_mention(user) -> str:
        """Форматувати згадку користувача"""
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            return user.first_name
        else:
            return f"User_{user.id}"
    
    @staticmethod
    def format_timestamp(dt: datetime.datetime) -> str:
        """Форматувати час"""
        now = datetime.datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} дн. тому"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} год. тому"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} хв. тому"
        else:
            return "щойно"


class AdminUtils:
    """Утиліти для адміністратора"""
    
    @staticmethod
    def is_admin(user_id: int, admin_ids: list) -> bool:
        """Перевірити, чи є користувач адміністратором"""
        return user_id in admin_ids
    
    @staticmethod
    def log_admin_action(user_id: int, action: str):
        """Логувати дії адміністратора"""
        logger.info(f"Admin action: User {user_id} performed '{action}'")
    
    @staticmethod
    def format_system_info() -> str:
        """Форматувати системну інформацію"""
        import psutil
        import sys
        
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return (
                f"🖥 <b>Системна інформація:</b>\n"
                f"• CPU: {cpu_percent}%\n"
                f"• RAM: {memory.percent}% ({memory.used // 1024 // 1024} MB)\n"
                f"• Диск: {disk.percent}% ({disk.used // 1024 // 1024 // 1024} GB)\n"
                f"• Python: {sys.version.split()[0]}\n"
                f"• Uptime: {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
        except ImportError:
            return "📊 Системна інформація недоступна (psutil не встановлено)"


class SecurityUtils:
    """Утиліти безпеки"""
    
    @staticmethod
    def validate_callback_data(data: str) -> bool:
        """Валідувати callback дані"""
        allowed_callbacks = [
            "main_menu", "statistics", "recent_messages", "info", "help",
            "send_new", "admin_stats", "admin_broadcast", "admin_settings",
            "admin_logs", "confirm_yes", "confirm_no", "nav_prev", "nav_next"
        ]
        return data in allowed_callbacks
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистити текст від небезпечних символів"""
        # Видалити або замінити потенційно небезпечні символи
        dangerous_chars = ['<script>', '</script>', 'javascript:', 'onclick=']
        clean_text = text
        
        for char in dangerous_chars:
            clean_text = clean_text.replace(char, '')
        
        return clean_text.strip()
    
    @staticmethod
    def rate_limit_check(user_id: int, last_action_time: dict, cooldown: int = 1) -> bool:
        """Перевірка частоти запитів"""
        now = datetime.datetime.now()
        last_time = last_action_time.get(user_id)
        
        if last_time is None:
            last_action_time[user_id] = now
            return True
        
        if (now - last_time).seconds >= cooldown:
            last_action_time[user_id] = now
            return True
        
        return False


# Глобальні екземпляри
message_counter = MessageCounter()
user_tracker = UserTracker()
last_action_times = {}


def get_formatted_stats() -> str:
    """Отримати форматовану статистику"""
    msg_stats = message_counter.get_stats()
    user_stats = user_tracker.get_stats()
    
    return (
        f"📊 <b>Статистика боту</b>\n\n"
        f"📈 <b>Повідомлення:</b>\n"
        f"• Всього: {msg_stats['total']}\n"
        f"• Сьогодні: {msg_stats['today']}\n\n"
        f"👥 <b>Користувачі:</b>\n"
        f"• Всього: {user_stats['total_users']}\n"
        f"• Активні сьогодні: {user_stats['active_today']}\n\n"
        f"📅 Дата: {msg_stats['date']}"
    )