"""Inline клавиатуры для выбора параметров."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для команды /start."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать расчёт", callback_data="start_calculation")]
    ])


def get_quick_area_keyboard() -> InlineKeyboardMarkup:
    """Быстрые кнопки для площади."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10м²", callback_data="area_10"),
            InlineKeyboardButton(text="15м²", callback_data="area_15"),
            InlineKeyboardButton(text="20м²", callback_data="area_20"),
        ],
        [
            InlineKeyboardButton(text="25м²", callback_data="area_25"),
            InlineKeyboardButton(text="30м²", callback_data="area_30"),
            InlineKeyboardButton(text="Ввести своё", callback_data="area_custom"),
        ]
    ])


def get_corners_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора количества углов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="4", callback_data="corners_4"),
            InlineKeyboardButton(text="5", callback_data="corners_5"),
            InlineKeyboardButton(text="6", callback_data="corners_6"),
        ],
        [
            InlineKeyboardButton(text="7", callback_data="corners_7"),
            InlineKeyboardButton(text="8+", callback_data="corners_8"),
        ]
    ])


def get_quick_perimeter_keyboard() -> InlineKeyboardMarkup:
    """Быстрые кнопки для периметра."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="15м", callback_data="perimeter_15"),
            InlineKeyboardButton(text="20м", callback_data="perimeter_20"),
            InlineKeyboardButton(text="25м", callback_data="perimeter_25"),
        ],
        [
            InlineKeyboardButton(text="30м", callback_data="perimeter_30"),
            InlineKeyboardButton(text="Ввести своё", callback_data="perimeter_custom"),
        ]
    ])


def get_fabric_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора полотна."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🇨🇳 MSD — 902 ₽/м²\nКитай, стандартное качество",
            callback_data="fabric_msd"
        )],
        [InlineKeyboardButton(
            text="🇩🇪 BAUF — 974 ₽/м²\nГермания, плотное, гипоаллергенное",
            callback_data="fabric_bauf"
        )]
    ])


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора профиля."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📎 Со вставкой — БЕСПЛАТНО\n⚠️ Доп. углы (от 5-го): 103 ₽/шт",
            callback_data="profile_insert"
        )],
        [InlineKeyboardButton(
            text="🌑 Теневой ЭКОНОМ — 718 ₽/пог.м\nУглы слегка скруглённые",
            callback_data="profile_shadow_eco"
        )],
        [InlineKeyboardButton(
            text="🌑 Теневой EuroKraab — 1435 ₽/пог.м\n+ каждый угол 492 ₽",
            callback_data="profile_shadow_eurokraab"
        )],
        [InlineKeyboardButton(
            text="☁️ Парящий — 1845 ₽/пог.м\n+ каждый угол 492 ₽",
            callback_data="profile_floating"
        )],
        [InlineKeyboardButton(
            text="✨ Однородный AM1 — 3844 ₽/пог.м\nПремиум вариант",
            callback_data="profile_am1"
        )]
    ])


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no")
        ]
    ])


def get_cornice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора карниза."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ПК-14 (2 м) — 7688 ₽", callback_data="cornice_pk14_2m")],
        [InlineKeyboardButton(text="ПК-14 (3.2 м) — 12300 ₽", callback_data="cornice_pk14_3_2m")],
        [InlineKeyboardButton(text="ПК-14 (3.6 м) — 13838 ₽", callback_data="cornice_pk14_3_6m")],
        [InlineKeyboardButton(text="ПК-5 (цена за пог.м) — 2819 ₽/пог.м", callback_data="cornice_pk5")],
        [InlineKeyboardButton(text="БП-40 (цена за пог.м) — 1282 ₽/пог.м", callback_data="cornice_bp40")],
    ])


def get_spotlights_keyboard() -> InlineKeyboardMarkup:
    """Быстрые кнопки для светильников."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0", callback_data="spotlights_0"),
            InlineKeyboardButton(text="4", callback_data="spotlights_4"),
            InlineKeyboardButton(text="6", callback_data="spotlights_6"),
        ],
        [
            InlineKeyboardButton(text="8", callback_data="spotlights_8"),
            InlineKeyboardButton(text="10", callback_data="spotlights_10"),
            InlineKeyboardButton(text="Ввести своё", callback_data="spotlights_custom"),
        ]
    ])


def get_chandeliers_keyboard() -> InlineKeyboardMarkup:
    """Быстрые кнопки для люстр."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0", callback_data="chandeliers_0"),
            InlineKeyboardButton(text="1", callback_data="chandeliers_1"),
            InlineKeyboardButton(text="2", callback_data="chandeliers_2"),
            InlineKeyboardButton(text="3", callback_data="chandeliers_3"),
        ]
    ])


def get_result_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для результата расчёта."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Получить PDF-смету", callback_data="get_pdf")],
        [
            InlineKeyboardButton(text="🔄 Начать новый расчёт", callback_data="start_calculation"),
            InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_manager")
        ]
    ])

