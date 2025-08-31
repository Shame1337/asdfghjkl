# Швидкі команди для бота "Дніпро ОПЕРАТИВНИЙ"

## Локальне тестування
```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Створити .env файл
cp .env.example .env
# Редагувати .env та додати BOT_TOKEN і ADMIN_ID

# 3. Запустити бота локально
python test_local.py
# або
python main.py
```

## Railway Деплой
```bash
# 1. Ініціалізація git
git init
git add .
git commit -m "feat: Дніпро ОПЕРАТИВНИЙ bot ready for deploy"

# 2. Створення репозиторію на GitHub
# (через веб-інтерфейс GitHub)

# 3. Push до GitHub
git remote add origin https://github.com/YOUR_USERNAME/dnipro-operative-bot.git
git push -u origin main
```

## Перевірка webhook
```bash
# Встановлення webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://your-app.railway.app/webhook"

# Перевірка webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## Корисні команди Telegram API
```bash
# Отримати інформацію про бота
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Видалити webhook (для локального тестування)
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```