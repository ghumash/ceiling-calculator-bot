# Ceiling Calculator Bot

Telegram-бот для расчёта стоимости натяжных потолков.

## Установка

```bash
# 1. Установка зависимостей
poetry install

# 2. Настройка .env
cp .env.example .env
# Заполните обязательные поля в .env
```

## Настройка .env

**Обязательные параметры:**
- `BOT_TOKEN` - токен от [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` - ID администраторов через запятую (получить у [@userinfobot](https://t.me/userinfobot))
- `CONTACT_PHONE` - телефон менеджера
- `CONTACT_TELEGRAM` - Telegram контакт менеджера

## Запуск

```bash
poetry run python -m app.main
```

## Production

**Systemd:**
```ini
[Unit]
Description=Ceiling Calculator Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ceiling-calculator-bot
ExecStart=/path/to/ceiling-calculator-bot/.venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Screen/Tmux:**
```bash
screen -S ceiling-bot
poetry run python -m app.main
# Ctrl+A, D для отсоединения
```

## Структура

```
app/
├── main.py              # Точка входа
├── core/                # Конфигурация
│   └── config.py        # Настройки (Settings)
├── bot/                 # Логика бота
│   ├── handlers/        # Обработчики команд и FSM
│   ├── keyboards/       # Inline клавиатуры
│   ├── middlewares/     # Middleware (логирование)
│   └── states.py        # FSM состояния
├── services/            # Бизнес-логика
│   ├── calculator.py    # Расчёты стоимости
│   └── chat_logger.py   # Логирование диалогов
├── schemas/             # Pydantic модели данных
│   └── calculation.py   # Модель расчёта
├── templates/           # Текстовые сообщения
│   └── messages/        # Тексты для бота
└── utils/               # Вспомогательные функции
    ├── images.py        # Работа с изображениями
    ├── user.py          # Утилиты для пользователей
    └── validation.py    # Валидация ввода

static/
└── images/              # Изображения для бота
    ├── profiles/        # Фото профилей
    └── cornices/        # Фото карнизов

chat_logs/               # Логи диалогов (создаётся автоматически)
```

## Функционал

- Пошаговый расчёт стоимости натяжного потолка
- Автоматические уведомления админам о расчётах
- Логи всех диалогов в `chat_logs/user_*.txt`

## Технологии

- Python 3.13+
- aiogram 3.23.0
- pydantic 2.10.0
