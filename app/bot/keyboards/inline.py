"""Inline клавиатуры для выбора параметров."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура только с кнопкой 'Назад' для текстовых вопросов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
        ]
    )


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками 'Пропустить' и 'Назад'."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="skip_zero")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")],
        ]
    )


def get_skip_row_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками 'Назад' и 'Пропустить' в один ряд."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back"),
                InlineKeyboardButton(text="Пропустить", callback_data="skip_zero"),
            ],
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
                    text="🤖 Сделать предрасчёт сейчас", callback_data="method_bot"
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


def get_lighting_types_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    """Клавиатура множественного выбора типов освещения.
    
    Args:
        selected: Множество выбранных типов ('spotlights', 'tracks', 'light_lines', 'chandeliers')
    """
    def mark(key: str, label: str) -> str:
        return f"✅ {label}" if key in selected else label
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=mark("spotlights", "Точечные светильники"),
                    callback_data="toggle_spotlights"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=mark("tracks", "Трековые линии"),
                    callback_data="toggle_tracks"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=mark("light_lines", "Световые линии"),
                    callback_data="toggle_light_lines"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=mark("chandeliers", "Люстры"),
                    callback_data="toggle_chandeliers"
                ),
            ],
            [InlineKeyboardButton(text="Готово", callback_data="lighting_done")],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back"),
                InlineKeyboardButton(text="Пропустить", callback_data="lighting_skip"),
            ],
        ]
    )


def get_track_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа треков."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Накладные", callback_data="track_surface"),
                InlineKeyboardButton(text="Встроенные", callback_data="track_built_in"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back"),
                InlineKeyboardButton(text="Пропустить", callback_data="track_none"),
            ],
        ]
    )


def get_wall_finish_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора чистовых работ стен."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="wall_yes"),
                InlineKeyboardButton(text="Нет", callback_data="wall_no"),
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
    """Клавиатура выбора параметра для редактирования."""
    area = data.get("area", "—")
    profile = data.get("profile_type", "—")
    cornice = data.get("cornice_type")
    cornice_length = data.get("cornice_length", 0)
    spotlights = data.get("spotlights", 0)
    track_type = data.get("track_type")
    track_length = data.get("track_length", 0)
    light_lines = data.get("light_lines", 0)
    chandeliers = data.get("chandeliers", 0)
    wall_finish = data.get("wall_finish")
    
    profile_names = {"insert": "Со вставкой", "shadow": "Теневой", "floating": "Парящий"}
    profile_display = profile_names.get(profile, profile)
    
    cornice_names = {"pk5": "ПК-5", "am1": "АМ-1", "pk14": "ПК-14", "bpp": "БП-П", "bp40": "БП-40"}
    cornice_display = f"{cornice_names.get(cornice, cornice)} ({cornice_length}м)" if cornice and cornice_length > 0 else "нет"
    
    track_names = {"surface": "Накладные", "built_in": "Встроенные"}
    track_display = f"{track_names.get(track_type, '')} ({track_length}м)" if track_type else "нет"
    
    light_display = f"{light_lines} м" if light_lines else "нет"
    wall_display = "Да" if wall_finish else "Нет"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📐 Площадь: {area} м²", callback_data="edit_area")],
            [InlineKeyboardButton(text=f"🔲 Профиль: {profile_display}", callback_data="edit_profile")],
            [InlineKeyboardButton(text=f"📏 Карниз: {cornice_display}", callback_data="edit_cornice")],
            [InlineKeyboardButton(text=f"💡 Светильники: {spotlights} шт", callback_data="edit_spotlights")],
            [InlineKeyboardButton(text=f"🚃 Треки: {track_display}", callback_data="edit_tracks")],
            [InlineKeyboardButton(text=f"💫 Световые линии: {light_display}", callback_data="edit_light_lines")],
            [InlineKeyboardButton(text=f"🔦 Люстры: {chandeliers} шт", callback_data="edit_chandeliers")],
            [InlineKeyboardButton(text=f"🧱 Чистовые работы: {wall_display}", callback_data="edit_wall_finish")],
            [InlineKeyboardButton(text="⬅️ Назад к результату", callback_data="back_to_result")],
        ]
    )
