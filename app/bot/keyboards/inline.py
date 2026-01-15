"""Inline клавиатуры для выбора параметров."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой 'Назад' для текстовых вопросов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
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
    new_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")])
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
                    text="Обычный со вставкой", callback_data="profile_insert"
                )
            ],
            [InlineKeyboardButton(text="Теневой", callback_data="profile_shadow")],
            [InlineKeyboardButton(text="Парящий (без стоимости ленты)", callback_data="profile_floating")],
        ]
    )
    return add_back_button(keyboard)


def get_cornice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора карниза."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="ПК-5", callback_data="cornice_pk5"),
                InlineKeyboardButton(text="АМ-1", callback_data="cornice_am1"),
            ],
            [
                InlineKeyboardButton(text="ПК-14", callback_data="cornice_pk14"),
                InlineKeyboardButton(text="БП-П", callback_data="cornice_bpp"),
            ],
            [
                InlineKeyboardButton(text="БП-40", callback_data="cornice_bp40"),
                InlineKeyboardButton(text="Без карнизов", callback_data="cornice_none"),
            ],
        ]
    )
    return add_back_button(keyboard)


def get_result_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после результата."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить параметры", callback_data="edit_params"
                )
            ],
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
            [
                InlineKeyboardButton(
                    text="📐 Бесплатный выезд замерщика", callback_data="order_measurement"
                )
            ],
        ]
    )


def get_edit_params_keyboard(data: dict) -> InlineKeyboardMarkup:
    """Клавиатура выбора параметра для редактирования.
    
    Args:
        data: Данные текущего расчёта
        
    Returns:
        Клавиатура с параметрами
    """
    area = data.get("area", "—")
    profile = data.get("profile_type", "—")
    cornice = data.get("cornice_type")
    cornice_length = data.get("cornice_length", 0)
    spotlights = data.get("spotlights", 0)
    chandeliers = data.get("chandeliers", 0)
    
    # Форматирование значений
    profile_names = {"insert": "Со вставкой", "shadow": "Теневой", "floating": "Парящий"}
    profile_display = profile_names.get(profile, profile)
    
    cornice_names = {"pk5": "ПК-5", "am1": "АМ-1", "pk14": "ПК-14", "bpp": "БП-П", "bp40": "БП-40"}
    if cornice and cornice_length > 0:
        cornice_display = f"{cornice_names.get(cornice, cornice)} ({cornice_length}м)"
    else:
        cornice_display = "нет"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📐 Площадь: {area} м²", callback_data="edit_area")],
            [InlineKeyboardButton(text=f"🔲 Профиль: {profile_display}", callback_data="edit_profile")],
            [InlineKeyboardButton(text=f"📏 Карниз: {cornice_display}", callback_data="edit_cornice")],
            [InlineKeyboardButton(text=f"💡 Светильники: {spotlights} шт", callback_data="edit_spotlights")],
            [InlineKeyboardButton(text=f"🔦 Люстры: {chandeliers} шт", callback_data="edit_chandeliers")],
            [InlineKeyboardButton(text="⬅️ Назад к результату", callback_data="back_to_result")],
        ]
    )
