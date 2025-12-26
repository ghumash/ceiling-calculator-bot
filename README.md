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

**Опционально (цены, есть значения по умолчанию):**
- `CEILING_BASE_PRICE=902` - цена за м² потолка
- `MIN_AREA_FOR_CALCULATION=20` - минимальная площадь для расчёта
- `PROFILE_SHADOW_PRICE=718` - цена теневого профиля за м
- `PROFILE_FLOATING_PRICE=1845` - цена парящего профиля за м
- `PERIMETER_COEFFICIENT=1.4` - коэффициент расчёта периметра
- `CORNICE_PK14_PRICE=3844` - цена карниза ПК-14 за м
- `CORNICE_PK5_PRICE=2819` - цена карниза ПК-5 за м
- `CORNICE_BP40_PRICE=1282` - цена карниза БП-40 за м
- `SPOTLIGHT_PRICE=513` - цена установки светильника
- `CHANDELIER_PRICE=550` - цена установки люстры
- `LOG_LEVEL=INFO` - уровень логирования

## Изображения

**Рекомендуется:**
- `static/images/profiles/profiles_all.jpg` - единое фото с тремя профилями
- `static/images/cornices/cornices_all.jpg` (или `carnices_all.jpg`) - единое фото с тремя карнизами

**Альтернатива:** отдельные файлы `insert.jpg`, `shadow_eco.jpg`, `floating.jpg` для профилей и `pk14.jpg`, `pk5.jpg`, `bp40.jpg` для карнизов.

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
├── core/config.py       # Настройки
├── bot/                 # Логика бота
│   ├── handlers/        # Обработчики
│   ├── keyboards/       # Клавиатуры
│   └── states.py        # FSM состояния
├── services/            # Бизнес-логика
├── schemas/             # Pydantic модели
└── templates/           # Тексты сообщений
```

## Функционал

- Пошаговый расчёт стоимости натяжного потолка
- Автоматические уведомления админам о расчётах
- Логи всех диалогов в `chat_logs/user_*.txt`

## Технологии

- Python 3.13+
- aiogram 3.23.0
- pydantic 2.10.0
