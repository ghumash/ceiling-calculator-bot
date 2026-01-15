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
- `CONTACT_PHONE` - телефон менеджера (например: `+7 (926) 103-43-03`)
- `CONTACT_TELEGRAM` - Telegram username менеджера (например: `@manager`)

**Уведомления (можно использовать все варианты одновременно):**
- `CHANNEL_CHAT_ID` - ID канала (публичный архив)
- `GROUP_CHAT_ID` - ID группы (обсуждения)
- `ADMIN_IDS` - ID менеджеров (личные уведомления)

**Как получить CHAT_ID:**
1. Добавьте бота в канал/группу как админа
2. Добавьте бота в бот с названием @id_bot в настройках
3. Нажать на пункт канал/группа и скопировать id

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
- Выбор типа профиля (обычный, теневой, парящий)
- Расчёт карнизов (ПК-14, ПК-5, БП-40)
- Расчёт освещения (светильники, люстры)
- Заказ бесплатного замера
- Автоматические уведомления в группу о расчётах и заказах
- Логи всех диалогов в `chat_logs/user_*.txt`

## Технологии

- Python 3.13+
- aiogram 3.23.0
- pydantic 2.10.0
