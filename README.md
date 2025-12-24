# Ceiling Calculator Bot

Telegram-бот для автоматизации консультаций и расчёта стоимости натяжных потолков.

## Технологический стек

- Python 3.13-3.14
- aiogram 3.23.0
- pydantic 2.10.0
- pillow 11.1.0

## Установка

### 1. Установка зависимостей Python

```bash
poetry install
```

### 2. Настройка .env

Скопируйте `.env.example` в `.env` и заполните необходимые параметры:

```bash
cp .env.example .env
```

Обязательно укажите:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_IDS` - ID администраторов (через запятую)

### 3. Подготовка изображений

Создайте директории и добавьте изображения материалов:

```bash
mkdir -p static/images/{fabrics,profiles,cornices,lighting}
```

Добавьте изображения:
- `static/images/fabrics/msd.jpg`
- `static/images/fabrics/bauf.jpg`
- `static/images/profiles/insert.jpg`
- `static/images/profiles/shadow_eco.jpg`
- `static/images/profiles/shadow_eurokraab.jpg`
- `static/images/profiles/floating.jpg`
- `static/images/profiles/am1.jpg`
- `static/images/cornices/pk14.jpg`
- `static/images/cornices/pk5.jpg`
- `static/images/cornices/bp40.jpg`
- `static/images/lighting/spotlights.jpg`
- `static/images/lighting/chandeliers.jpg`

## Запуск

```bash
poetry run python -m app.main
```

## Структура проекта

```
ceiling-calculator-bot/
├── app/
│   ├── main.py              # Точка входа
│   ├── core/                # Конфигурация
│   ├── bot/                 # Логика бота
│   │   ├── handlers/        # Обработчики
│   │   ├── keyboards/       # Клавиатуры
│   │   ├── middlewares/     # Middleware
│   │   └── states.py        # FSM состояния
│   ├── services/            # Бизнес-логика
│   ├── schemas/             # Pydantic модели
│   └── templates/           # Шаблоны
├── static/                  # Статические файлы
└── chat_logs/              # Логи чатов
```

## Функционал

### Для пользователей

1. **Расчёт стоимости** - пошаговый диалог с выбором параметров
2. **Детальная смета** - подробный расчёт стоимости в сообщении
3. **Изображения материалов** - визуальный выбор полотен, профилей, карнизов

### Для администраторов

- `/stats` - статистика бота
- `/history <user_id>` - история чата с пользователем
- `/broadcast <текст>` - рассылка сообщений всем пользователям
- `/prices` - просмотр текущих цен

## Особенности

- **Без базы данных** - все данные хранятся в FSM (в памяти)
- **Логирование чатов** - все диалоги сохраняются в текстовые файлы
- **Уведомления админу** - автоматические уведомления о новых расчётах
- **Валидация данных** - проверка корректности ввода через Pydantic
- **Обработка ошибок** - graceful handling всех исключений

## Лицензия

MIT

