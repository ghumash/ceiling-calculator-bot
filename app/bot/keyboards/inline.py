"""Inline клавиатуры для выбора параметров."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой 'Назад' для текстовых вопросов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="go_back")]
        ]
    )


def add_back_button(keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Добавляет кнопку 'Назад' в клавиатуру.
    
    Args:
        keyboard: Существующая клавиатура
        
    Returns:
        Клавиатура с добавленной кнопкой 'Назад'
    """
    new_rows = keyboard.inline_keyboard.copy()
    new_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=new_rows)


def get_contact_method_keyboard() -> InlineKeyboardMarkup:
    """Выбор способа связи."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Сделать предрасчёт с помощью бота", callback_data="method_bot"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Связаться с менеджером", callback_data="method_manager"
                )
            ],
        ]
    )


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора профиля."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✦ Обычный со вставкой", callback_data="profile_insert"
                )
            ],
            [InlineKeyboardButton(text="✦ Теневой", callback_data="profile_shadow")],
            [InlineKeyboardButton(text="✦ Парящий", callback_data="profile_floating")],
        ]
    )
    return add_back_button(keyboard)


def get_cornice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора карниза."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ПК-14", callback_data="cornice_pk14")],
            [InlineKeyboardButton(text="ПК-5", callback_data="cornice_pk5")],
            [InlineKeyboardButton(text="БП-40", callback_data="cornice_bp40")],
        ]
    )
    return add_back_button(keyboard)


def get_result_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после результата."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Начать новый расчёт", callback_data="start_calculation"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📞 Связаться с менеджером", callback_data="method_manager"
                )
            ],
        ]
    )
