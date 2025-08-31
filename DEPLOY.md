# 🚀 Інструкція з деплою бота на Railway

## Крок 1: Підготовка бота в Telegram

1. **Створіть бота в BotFather:**
   - Відкрийте @BotFather в Telegram
   - Надішліть `/newbot`
   - Введіть назву: `Дніпро ОПЕРАТИВНИЙ 🇺🇦`
   - Введіть username: `dnipro_operative_bot` (або інший доступний)
   - Збережіть отриманий TOKEN

2. **Налаштуйте бота:**
   ```
   /setdescription - Оперативний бот для збору інформації про події в Дніпрі та області
   /setabouttext - 🇺🇦 Дніпро ОПЕРАТИВНИЙ - збір та поширення оперативної інформації
   /setuserpic - завантажте аватар (прапор України або символіка Дніпра)
   ```

## Крок 2: Підготовка коду

1. **Завантажте код на GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Дніпро ОПЕРАТИВНИЙ bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/dnipro-operative-bot.git
   git push -u origin main
   ```

## Крок 3: Деплой на Railway

1. **Зайдіть на Railway:**
   - Відкрийте https://railway.app
   - Увійдіть через GitHub

2. **Створіть новий проект:**
   - Натисніть "New Project"
   - Оберіть "Deploy from GitHub repo"
   - Виберіть ваш репозиторій

3. **Налаштуйте змінні середовища:**
   Перейдіть в Variables та додайте:
   ```
   BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
   WEBHOOK_URL=https://YOUR_APP_NAME.railway.app
   ADMIN_ID=YOUR_TELEGRAM_USER_ID
   ```

4. **Отримайте ваш ADMIN_ID:**
   - Напишіть @userinfobot в Telegram
   - Надішліть `/start`
   - Скопіюйте ваш ID

5. **Налаштуйте домен:**
   - В Railway перейдіть в Settings → Domains
   - Згенеруйте домен або додайте кастомний
   - Скопіюйте URL та оновіть WEBHOOK_URL

## Крок 4: Тестування

1. **Перевірте деплой:**
   - Подивіться логи в Railway
   - Переконайтесь, що бот запустився без помилок

2. **Тестуйте бота:**
   - Знайдіть вашого бота в Telegram
   - Надішліть `/start`
   - Перевірте всі кнопки та функції
   - Надішліть тестове фото/відео
   - Перевірте отримання повідомлень адміном

## Крок 5: Фінальне налаштування

1. **Налаштуйте webhook:**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-app.railway.app/webhook"}'
   ```

2. **Перевірте webhook:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
   ```

## 🔧 Налаштування для продакшн

### Автоматичні бекапи
```python
# Додайте в main.py
import schedule
import time

def backup_data():
    # Логіка бекапу статистики
    pass

schedule.every().day.at("02:00").do(backup_data)
```

### Моніторинг
1. **Railway Logs** - перевіряйте регулярно
2. **Uptime Robot** - для моніторингу доступності
3. **Telegram повідомлення** - про критичні помилки

### Безпека
1. **Ніколи не публікуйте** BOT_TOKEN в коді
2. **Використовуйте** environment variables
3. **Обмежте доступ** до адмін функцій
4. **Логуйте** всі важливі дії

## 📱 Використання бота

### Для користувачів:
- `/start` - запуск бота
- Надсилання фото/відео з описом
- Текстові повідомлення про події
- Використання inline-кнопок для навігації

### Для адміна:
- `/admin` - адмін панель
- Перегляд статистики
- Отримання всіх повідомлень користувачів

## 🔍 Моніторинг та аналітика

### Логи Railway:
```bash
# Командний рядок Railway CLI
railway logs
```

### Файл bot.log:
- Всі дії користувачів
- Помилки та винятки
- Системні події

## 🆘 Troubleshooting

### Бот не відповідає:
1. Перевірте логи Railway
2. Перевірте webhook: `/getWebhookInfo`
3. Перевірте змінні середовища

### Помилки з базою даних:
1. Перевірте права доступу
2. Перевірте з'єднання

### Помилки з медіа:
1. Перевірте розмір файлів (макс 50MB)
2. Перевірте формати (jpg, png, mp4)

---

**🇺🇦 Слава Україні! Разом до перемоги! 🇺🇦**