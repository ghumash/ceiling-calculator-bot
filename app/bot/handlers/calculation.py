"""Обработчик FSM диалога расчёта."""

import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User

from app.bot.states import CalculationStates
from app.bot.keyboards.inline import (
    get_profile_keyboard,
    get_cornice_keyboard,
    get_result_keyboard,
    get_back_keyboard,
    get_skip_row_keyboard,
    get_contact_method_keyboard,
    get_edit_params_keyboard,
    get_spotlight_types_keyboard,
    get_track_types_keyboard,
    get_wall_finish_keyboard,
    get_lighting_types_keyboard,
)
from app.templates.messages.texts import (
    AREA_QUESTION,
    AREA_ACCEPTED,
    AREA_INVALID_INPUT,
    PROFILE_QUESTION,
    PROFILE_ACCEPTED,
    CORNICE_LENGTH_QUESTION,
    CORNICE_TYPE_QUESTION,
    CORNICE_ACCEPTED,
    NO_CORNICE,
    CORNICE_INVALID_INPUT,
    LIGHTING_TYPES_QUESTION,
    NO_LIGHTING,
    SPOTLIGHT_TYPES_QUESTION,
    NO_SPOTLIGHTS,
    SPOTLIGHTS_BUILTIN_QUESTION,
    SPOTLIGHTS_SURFACE_QUESTION,
    SPOTLIGHTS_PENDANT_QUESTION,
    SPOTLIGHTS_ACCEPTED,
    SPOTLIGHTS_INVALID_INPUT,
    TRACK_TYPES_QUESTION,
    NO_TRACKS,
    TRACK_SURFACE_LENGTH_QUESTION,
    TRACK_BUILTIN_LENGTH_QUESTION,
    TRACK_LENGTH_ACCEPTED,
    TRACK_INVALID_INPUT,
    LIGHT_LINES_QUESTION,
    LIGHT_LINES_ACCEPTED,
    LIGHT_LINES_INVALID_INPUT,
    CHANDELIERS_QUESTION,
    CHANDELIERS_ACCEPTED,
    CHANDELIERS_INVALID_INPUT,
    WALL_FINISH_QUESTION,
    WALL_FINISH_ACCEPTED,
    RESULT_MESSAGE,
    ADMIN_REPORT,
    WELCOME_MESSAGE,
    NAME_QUESTION,
    NAME_ACCEPTED,
    NAME_INVALID_INPUT,
    PHONE_QUESTION,
    PHONE_ACCEPTED,
    PHONE_INVALID_INPUT,
    ADDRESS_QUESTION,
    ADDRESS_ACCEPTED,
    ADDRESS_INVALID_INPUT,
    MEASUREMENT_THANK_YOU,
    MEASUREMENT_REPORT,
    EDIT_PARAMS_MESSAGE,
    get_profile_name,
    get_cornice_name,
    get_cornice_validation_error,
    get_count_validation_error,
    format_ceiling_details,
    format_profile_details,
    format_cornice_details,
    format_spotlights_details,
    format_chandeliers_details,
    format_track_details,
    format_light_lines_details,
    with_progress,
)
from app.services.chat_logger import chat_logger
from app.services.calculator import calculate_total
from app.schemas.calculation import CalculationData
from app.core.config import settings
from app.utils.validation import parse_float, parse_int, validate_range, validate_phone, normalize_phone
from app.utils.user import get_user_display_name
from app.utils.images import send_image_if_exists
from app.utils.callback import safe_answer_callback

logger = logging.getLogger(__name__)

# Базовые номера шагов
STEP_AREA = 1
STEP_PROFILE = 2
STEP_CORNICE_TYPE = 3
STEP_CORNICE_LENGTH = 4
STEP_LIGHTING_TYPES = 5

# Количество базовых шагов (до выбора освещения)
BASE_STEPS = 5


def calculate_total_steps(selected_lighting: set[str] | None, all_steps: bool = False) -> int:
    """Рассчитывает общее количество шагов.
    
    Args:
        selected_lighting: Выбранные типы освещения
        all_steps: Если True — все шаги последовательно (режим "Все по шагам")
    """
    if all_steps or selected_lighting is None:
        return 10  # Все шаги: 5 базовых + 4 освещения + чистовые
    
    steps = BASE_STEPS  # Базовые шаги
    if "spotlights" in selected_lighting:
        steps += 1
    if "tracks" in selected_lighting:
        steps += 2  # Тип + длина
    if "light_lines" in selected_lighting:
        steps += 1
    if "chandeliers" in selected_lighting:
        steps += 1
    steps += 1  # Чистовые работы
    return steps


def get_dynamic_step(base_step: int, selected_lighting: set[str] | None, lighting_type: str) -> int:
    """Возвращает номер шага для типа освещения с учётом выбора.
    
    Args:
        base_step: Номер шага выбора освещения (STEP_LIGHTING_TYPES)
        selected_lighting: Выбранные типы освещения
        lighting_type: Тип освещения ('spotlights', 'tracks', 'track_length', 'light_lines', 'chandeliers', 'wall_finish')
    """
    if selected_lighting is None:
        # Режим "Все по шагам" — фиксированные номера
        mapping = {
            "spotlights": 6,
            "tracks": 7,
            "track_length": 8,
            "light_lines": 9,
            "chandeliers": 10,
            "wall_finish": 11,
        }
        return mapping.get(lighting_type, base_step + 1)
    
    step = base_step
    order = ["spotlights", "tracks", "track_length", "light_lines", "chandeliers", "wall_finish"]
    
    for lt in order:
        if lt == lighting_type:
            return step + 1
        if lt == "track_length":
            if "tracks" in selected_lighting:
                step += 1
        elif lt == "wall_finish":
            step += 1
        elif lt in selected_lighting:
            step += 1
    
    return step + 1


router = Router()


# ============================================
# ВОЗВРАТ НАЗАД
# ============================================


def _get_previous_lighting_state(data: dict) -> CalculationStates:
    """Определяет предыдущее состояние перед освещением.
    
    Args:
        data: Данные состояния
        
    Returns:
        Предыдущее состояние
    """
    if data.get("cornice_length", 0) == 0:
        return CalculationStates.choosing_cornice_type
    return CalculationStates.entering_cornice_length


async def _go_back_to_contact_method(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к выбору способа связи."""
    await state.clear()
    user_name = callback.from_user.first_name or "Пользователь"
    welcome_text = WELCOME_MESSAGE.format(name=user_name)
    await callback.message.answer(
        text=welcome_text,
        reply_markup=get_contact_method_keyboard(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CalculationStates.choosing_contact_method)
    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=welcome_text, is_bot=True
    )


async def _go_back_to_area(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к вводу площади."""
    await state.update_data(profile_type=None, previous_state=CalculationStates.choosing_contact_method)
    await ask_area(callback.message, state, user_id)


async def _go_back_to_profile(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к выбору профиля."""
    await state.update_data(cornice_type=None, cornice_length=None, previous_state=CalculationStates.choosing_profile)
    await _ask_profile(callback.message, state, user_id)


async def _go_back_to_cornice_type(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к выбору типа карниза."""
    await state.update_data(cornice_length=None, previous_state=CalculationStates.choosing_profile)
    await _ask_cornice_type(callback.message, state, user_id)


async def _go_back_to_cornice_length(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к вводу длины карнизов."""
    await state.update_data(previous_state=CalculationStates.choosing_cornice_type)
    await _ask_cornice_length(callback.message, state, user_id)


async def _go_back_to_spotlights(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат к вводу светильников."""
    await state.update_data(spotlights=None)
    previous_state = _get_previous_lighting_state(data)
    await state.update_data(previous_state=previous_state)
    
    if data.get("cornice_length", 0) == 0:
        await _ask_cornice_type(callback.message, state, user_id)
    else:
        await _ask_cornice_length(callback.message, state, user_id)


async def _go_back_to_result(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к результату расчёта."""
    await state.update_data(customer_name=None, previous_state=CalculationStates.showing_result)
    # Возвращаемся к результату - показываем его снова
    data = await state.get_data()
    
    # Проверка обязательных полей
    if "area" not in data or "profile_type" not in data:
        await callback.message.answer(
            "❌ Ошибка: не все обязательные параметры заполнены. Пожалуйста, начните расчёт заново.",
            parse_mode=ParseMode.HTML
        )
        return
    
    calculation = calculate_total(data)
    area_note, profile_info, lighting_info = _format_result_info(calculation)
    
    result_text = RESULT_MESSAGE.format(
        area=calculation.area,
        area_note=area_note,
        cornice_info=profile_info,
        lighting_info=lighting_info,
        total=calculation.total_cost,
    )
    
    await callback.message.answer(result_text, reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.showing_result)
    chat_logger.log_message(
        user_id=user_id, username="БОТ", message="◀️ Возврат к результату", is_bot=True
    )


async def _go_back_to_name(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к вводу имени."""
    await state.update_data(phone=None, previous_state=CalculationStates.showing_result)
    await _ask_name(callback.message, state, user_id)


async def _go_back_to_phone(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к вводу телефона."""
    await state.update_data(address=None, previous_state=CalculationStates.entering_name)
    await _ask_phone(callback.message, state, user_id)


async def _go_back_from_light_lines(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат из световых линий."""
    all_steps = data.get("all_lighting_steps", False)
    selected = data.get("selected_lighting", set())
    
    if all_steps:
        if data.get("track_type"):
            await _ask_track_length(callback.message, state, user_id)
        else:
            await _ask_track_types(callback.message, state, user_id)
    elif "tracks" in selected:
        await _ask_track_length(callback.message, state, user_id)
    elif "spotlights" in selected:
        await _ask_spotlight_types(callback.message, state, user_id)
    else:
        await _ask_lighting_types(callback.message, state, user_id)


async def _go_back_to_cornice(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат к карнизу из выбора освещения."""
    if data.get("cornice_type"):
        await _ask_cornice_length(callback.message, state, user_id)
    else:
        await _ask_cornice_type(callback.message, state, user_id)


async def _go_back_to_lighting_types(callback: CallbackQuery, state: FSMContext, user_id: int) -> None:
    """Возврат к выбору типов освещения."""
    await state.update_data(spotlights=None)
    await _ask_lighting_types(callback.message, state, user_id)


async def _go_back_from_tracks(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат из треков."""
    all_steps = data.get("all_lighting_steps", False)
    selected = data.get("selected_lighting", set())
    
    if all_steps:
        await _ask_spotlight_types(callback.message, state, user_id)
    elif "spotlights" in selected:
        await _ask_spotlight_types(callback.message, state, user_id)
    else:
        await _ask_lighting_types(callback.message, state, user_id)


async def _go_back_from_chandeliers(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат из люстр."""
    all_steps = data.get("all_lighting_steps", False)
    selected = data.get("selected_lighting", set())
    
    if all_steps:
        await _ask_light_lines(callback.message, state, user_id)
    elif "light_lines" in selected:
        await _ask_light_lines(callback.message, state, user_id)
    elif "tracks" in selected:
        await _ask_track_length(callback.message, state, user_id)
    elif "spotlights" in selected:
        await _ask_spotlight_types(callback.message, state, user_id)
    else:
        await _ask_lighting_types(callback.message, state, user_id)


async def _go_back_from_wall_finish(callback: CallbackQuery, state: FSMContext, user_id: int, data: dict) -> None:
    """Возврат из чистовых работ."""
    all_steps = data.get("all_lighting_steps", False)
    selected = data.get("selected_lighting", set())
    
    if all_steps:
        await _ask_chandeliers(callback.message, state, user_id)
    elif "chandeliers" in selected:
        await _ask_chandeliers(callback.message, state, user_id)
    elif "light_lines" in selected:
        await _ask_light_lines(callback.message, state, user_id)
    elif "tracks" in selected:
        await _ask_track_length(callback.message, state, user_id)
    elif "spotlights" in selected:
        await _ask_spotlight_types(callback.message, state, user_id)
    else:
        await _ask_lighting_types(callback.message, state, user_id)


@router.callback_query(F.data == "skip_zero")
async def skip_with_zero(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Пропустить' — устанавливает 0."""
    await safe_answer_callback(callback)
    
    current_state = await state.get_state()
    user_id = callback.from_user.id
    data = await state.get_data()
    
    if current_state == CalculationStates.entering_light_lines:
        editing_mode = data.get("editing_mode", False)
        all_steps = data.get("all_lighting_steps", False)
        await state.update_data(light_lines=0, editing_mode=False)
        await callback.message.answer("✅ <b>Световые линии:</b> не требуются", parse_mode=ParseMode.HTML)
        if editing_mode:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        elif all_steps:
            await _ask_chandeliers(callback.message, state, user_id)
        else:
            await _process_next_lighting(callback.message, state, user_id)
    elif current_state == CalculationStates.entering_chandeliers:
        await _process_chandeliers(callback.message, state, 0, callback.from_user)


@router.callback_query(F.data == "go_back")
async def go_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата на предыдущий шаг."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    current_state = await state.get_state()
    user_id = callback.from_user.id
    
    handlers = {
        CalculationStates.waiting_for_area: _go_back_to_contact_method,
        CalculationStates.choosing_profile: _go_back_to_area,
        CalculationStates.choosing_cornice_type: _go_back_to_profile,
        CalculationStates.entering_cornice_length: _go_back_to_cornice_type,
        CalculationStates.choosing_lighting_types: lambda cb, st, uid: _go_back_to_cornice(cb, st, uid, data),
        CalculationStates.choosing_spotlight_types: lambda cb, st, uid: _ask_lighting_types(cb.message, st, uid),
        CalculationStates.entering_spotlights_builtin: lambda cb, st, uid: _ask_spotlight_types(cb.message, st, uid),
        CalculationStates.entering_spotlights_surface: lambda cb, st, uid: _ask_spotlight_types(cb.message, st, uid),
        CalculationStates.entering_spotlights_pendant: lambda cb, st, uid: _ask_spotlight_types(cb.message, st, uid),
        CalculationStates.choosing_track_types: lambda cb, st, uid: _go_back_from_tracks(cb, st, uid, data),
        CalculationStates.entering_track_surface_length: lambda cb, st, uid: _ask_track_types(cb.message, st, uid),
        CalculationStates.entering_track_builtin_length: lambda cb, st, uid: _ask_track_types(cb.message, st, uid),
        CalculationStates.entering_light_lines: lambda cb, st, uid: _go_back_from_light_lines(cb, st, uid, data),
        CalculationStates.entering_chandeliers: lambda cb, st, uid: _go_back_from_chandeliers(cb, st, uid, data),
        CalculationStates.choosing_wall_finish: lambda cb, st, uid: _go_back_from_wall_finish(cb, st, uid, data),
        CalculationStates.entering_phone: lambda cb, st, uid: _go_back_to_result(cb, st, uid),
        CalculationStates.entering_address: lambda cb, st, uid: _go_back_to_phone(cb, st, uid),
    }
    
    handler = handlers.get(current_state)
    if handler:
        await handler(callback, state, user_id)
    
    chat_logger.log_message(
        user_id=user_id,
        username="БОТ",
        message="⬅️ Возврат на предыдущий шаг",
        is_bot=True,
    )


# ============================================
# ПЛОЩАДЬ
# ============================================


async def ask_area(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает площадь помещения."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.choosing_contact_method)
    await message.answer(with_progress(AREA_QUESTION, STEP_AREA), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.waiting_for_area)

    chat_logger.log_message(user_id=user_id, username="БОТ", message=AREA_QUESTION, is_bot=True)


@router.message(CalculationStates.waiting_for_area)
async def process_area_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода площади."""
    if not message.text:
        await message.answer(AREA_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    area = parse_float(message.text)
    if area is None:
        await message.answer(AREA_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Площадь: {area} м²",
        is_bot=False,
    )

    await _process_area(message, state, area, message.from_user.id)


async def _process_area(message: Message, state: FSMContext, area: float, user_id: int) -> None:
    """Сохраняет площадь и переходит к выбору профиля или результату."""
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(area=area, editing_mode=False)

    response = AREA_ACCEPTED.format(area=area)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=response, is_bot=True)

    if editing_mode:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_profile(message, state, user_id)


# ============================================
# ПРОФИЛЬ
# ============================================


async def _ask_profile(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает тип профиля."""
    await state.update_data(previous_state=CalculationStates.waiting_for_area)
    
    profiles_path = Path(settings.profiles_dir)
    profile_photo_path = profiles_path / "profiles_all.jpg"
    fallback_paths = ["insert.jpg", "shadow_eco.jpg", "floating.jpg"]
    
    await send_image_if_exists(message, profile_photo_path, fallback_paths)

    await message.answer(with_progress(PROFILE_QUESTION, STEP_PROFILE), reply_markup=get_profile_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_profile)

    chat_logger.log_message(user_id=user_id, username="БОТ", message=PROFILE_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_profile, F.data.startswith("profile_"))
async def process_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора профиля."""
    await safe_answer_callback(callback)

    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    profile_type = callback.data.replace("profile_", "")
    profile_name = get_profile_name(profile_type)

    await state.update_data(profile_type=profile_type, editing_mode=False)

    username = get_user_display_name(callback.from_user)
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Профиль: {profile_name}",
        is_bot=False,
    )

    response = PROFILE_ACCEPTED.format(profile_name=profile_name)
    await callback.message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=response, is_bot=True
    )

    if editing_mode:
        await _show_result_after_edit(callback.message, state, callback.from_user)
    else:
        await _ask_cornice_type(callback.message, state, callback.from_user.id)


# ============================================
# КАРНИЗЫ
# ============================================


async def _ask_cornice_type(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает тип карниза."""
    await state.update_data(previous_state=CalculationStates.choosing_profile)
    
    cornices_path = Path(settings.cornices_dir)
    cornice_photo_path = cornices_path / "cornices_all.jpg"
    fallback_paths = ["carnices_all.jpg", "pk14.jpg", "pk5.jpg", "bp40.jpg"]
    
    await send_image_if_exists(message, cornice_photo_path, fallback_paths)

    await message.answer(with_progress(CORNICE_TYPE_QUESTION, STEP_CORNICE_TYPE), reply_markup=get_cornice_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_cornice_type)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=CORNICE_TYPE_QUESTION, is_bot=True
    )


@router.callback_query(CalculationStates.choosing_cornice_type, F.data.startswith("cornice_"))
async def process_cornice_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора типа карниза."""
    await safe_answer_callback(callback)

    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    cornice_type = callback.data.replace("cornice_", "")
    
    # Если выбрано "Без карнизов"
    if cornice_type == "none":
        await state.update_data(cornice_type=None, cornice_length=0, editing_mode=False)
        await callback.message.answer(NO_CORNICE, parse_mode=ParseMode.HTML)
        chat_logger.log_message(
            user_id=callback.from_user.id, username="БОТ", message=NO_CORNICE, is_bot=True
        )
        
        if editing_mode:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _ask_lighting_types(callback.message, state, callback.from_user.id)
        return
    
    # Если выбран тип карниза - сохраняем и переходим к вопросу о длине
    cornice_name = get_cornice_name(cornice_type)
    await state.update_data(cornice_type=cornice_type)

    username = get_user_display_name(callback.from_user)
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Тип карниза: {cornice_name}",
        is_bot=False,
    )
    
    # Переход к вопросу о длине карнизов
    await _ask_cornice_length(callback.message, state, callback.from_user.id)


async def _ask_cornice_length(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает длину карнизов."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.choosing_cornice_type)
    await message.answer(with_progress(CORNICE_LENGTH_QUESTION, STEP_CORNICE_LENGTH), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_cornice_length)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=CORNICE_LENGTH_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_cornice_length)
async def process_cornice_length(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины карнизов."""
    if not message.text:
        await message.answer(CORNICE_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    length = parse_float(message.text)
    if length is None:
        await message.answer(CORNICE_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    if not validate_range(length, 0.0, settings.max_cornice_length):
        await message.answer(
            get_cornice_validation_error(settings.max_cornice_length),
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(cornice_length=length, editing_mode=False)

    cornice_type = data.get("cornice_type")
    cornice_name = get_cornice_name(cornice_type)
    
    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Длина карнизов: {length} пог.м",
        is_bot=False,
    )

    response = CORNICE_ACCEPTED.format(cornice_name=cornice_name, length=length)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=response, is_bot=True
    )

    if editing_mode:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_lighting_types(message, state, message.from_user.id)


# ============================================
# ОСВЕЩЕНИЕ - ВЫБОР ТИПОВ
# ============================================


async def _ask_lighting_types(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает выбор типов освещения."""
    await state.update_data(
        previous_state=CalculationStates.entering_cornice_length,
        selected_lighting=set(),
    )
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "lightnint_variants.jpg")
    
    total_steps = calculate_total_steps(None, all_steps=True)
    await message.answer(
        with_progress(LIGHTING_TYPES_QUESTION, STEP_LIGHTING_TYPES, total_steps),
        reply_markup=get_lighting_types_keyboard(set()),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CalculationStates.choosing_lighting_types)
    
    chat_logger.log_message(user_id=user_id, username="БОТ", message=LIGHTING_TYPES_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_lighting_types, F.data.startswith("toggle_"))
async def toggle_lighting_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Переключает выбор типа освещения."""
    await safe_answer_callback(callback)
    
    lighting_type = callback.data.replace("toggle_", "")
    data = await state.get_data()
    selected = data.get("selected_lighting", set())
    
    if isinstance(selected, list):
        selected = set(selected)
    
    if lighting_type in selected:
        selected.discard(lighting_type)
    else:
        selected.add(lighting_type)
    
    await state.update_data(selected_lighting=selected)
    
    total_steps = calculate_total_steps(selected if selected else None, all_steps=not selected)
    await callback.message.edit_text(
        with_progress(LIGHTING_TYPES_QUESTION, STEP_LIGHTING_TYPES, total_steps),
        reply_markup=get_lighting_types_keyboard(selected),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(CalculationStates.choosing_lighting_types, F.data == "lighting_done")
async def lighting_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершает выбор типов освещения и переходит к выбранным вопросам."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    selected = data.get("selected_lighting", set())
    
    if isinstance(selected, list):
        selected = set(selected)
    
    if not selected:
        await state.update_data(
            spotlights=0, track_type=None, track_length=0,
            light_lines=0, chandeliers=0, all_lighting_steps=False
        )
        await callback.message.answer(NO_LIGHTING, parse_mode=ParseMode.HTML)
        chat_logger.log_message(
            user_id=callback.from_user.id, username="БОТ", message=NO_LIGHTING, is_bot=True
        )
        await _ask_wall_finish(callback.message, state, callback.from_user.id)
        return
    
    await state.update_data(selected_lighting=selected, all_lighting_steps=False)
    await _process_next_lighting(callback.message, state, callback.from_user.id)


@router.callback_query(CalculationStates.choosing_lighting_types, F.data == "lighting_skip")
async def lighting_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропускает все вопросы освещения."""
    await safe_answer_callback(callback)
    
    await state.update_data(
        spotlights=0, track_type=None, track_length=0,
        light_lines=0, chandeliers=0,
        selected_lighting=set(), all_lighting_steps=False
    )
    await callback.message.answer(NO_LIGHTING, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=NO_LIGHTING, is_bot=True
    )
    await _ask_wall_finish(callback.message, state, callback.from_user.id)


async def _process_next_lighting(message: Message, state: FSMContext, user_id: int) -> None:
    """Переходит к следующему выбранному типу освещения."""
    data = await state.get_data()
    selected = data.get("selected_lighting", set())
    
    if isinstance(selected, list):
        selected = set(selected)
    
    # Порядок вопросов освещения
    order = ["spotlights", "tracks", "light_lines", "chandeliers"]
    
    for lighting_type in order:
        if lighting_type in selected:
            if lighting_type == "spotlights" and data.get("selected_spotlight_types") is None:
                await _ask_spotlight_types(message, state, user_id)
                return
            elif lighting_type == "tracks" and data.get("selected_track_types") is None:
                await _ask_track_types(message, state, user_id)
                return
            elif lighting_type == "light_lines" and data.get("light_lines") is None:
                await _ask_light_lines(message, state, user_id)
                return
            elif lighting_type == "chandeliers" and data.get("chandeliers") is None:
                await _ask_chandeliers(message, state, user_id)
                return
    
    # Все выбранные типы заполнены — переходим к чистовым работам
    await _ask_wall_finish(message, state, user_id)


# ============================================
# СВЕТИЛЬНИКИ - ВЫБОР ТИПОВ
# ============================================


async def _ask_spotlight_types(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает выбор типов светильников."""
    await state.update_data(selected_spotlight_types=set(), previous_state=CalculationStates.choosing_lighting_types)
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "spotlight_variants.jpg")
    
    data = await state.get_data()
    selected = data.get("selected_lighting", set())
    total_steps = calculate_total_steps(selected, False)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected, "spotlights")
    
    await message.answer(
        with_progress(SPOTLIGHT_TYPES_QUESTION, step, total_steps),
        reply_markup=get_spotlight_types_keyboard(set()),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CalculationStates.choosing_spotlight_types)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=SPOTLIGHT_TYPES_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_spotlight_types, F.data.startswith("toggle_spot_"))
async def toggle_spotlight_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Переключает выбор типа светильника."""
    await safe_answer_callback(callback)
    
    spot_type = callback.data.replace("toggle_spot_", "")
    data = await state.get_data()
    selected = set(data.get("selected_spotlight_types", set()))
    
    if spot_type in selected:
        selected.discard(spot_type)
    else:
        selected.add(spot_type)
    
    await state.update_data(selected_spotlight_types=selected)
    
    selected_lighting = data.get("selected_lighting", set())
    total_steps = calculate_total_steps(selected_lighting, False)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected_lighting, "spotlights")
    
    await callback.message.edit_text(
        with_progress(SPOTLIGHT_TYPES_QUESTION, step, total_steps),
        reply_markup=get_spotlight_types_keyboard(selected),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(CalculationStates.choosing_spotlight_types, F.data == "spotlights_done")
async def spotlights_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершает выбор типов светильников."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    selected = set(data.get("selected_spotlight_types", set()))
    
    if not selected:
        await state.update_data(spotlights_builtin=0, spotlights_surface=0, spotlights_pendant=0, editing_mode=False)
        await callback.message.answer(NO_SPOTLIGHTS, parse_mode=ParseMode.HTML)
        if editing_mode:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _process_next_lighting(callback.message, state, callback.from_user.id)
        return
    
    await _process_next_spotlight_type(callback.message, state, callback.from_user.id)


@router.callback_query(CalculationStates.choosing_spotlight_types, F.data == "spotlights_skip")
async def spotlights_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропускает светильники."""
    await safe_answer_callback(callback)
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    await state.update_data(spotlights_builtin=0, spotlights_surface=0, spotlights_pendant=0, editing_mode=False)
    await callback.message.answer(NO_SPOTLIGHTS, parse_mode=ParseMode.HTML)
    if editing_mode:
        await _show_result_after_edit(callback.message, state, callback.from_user)
    else:
        await _process_next_lighting(callback.message, state, callback.from_user.id)


async def _process_next_spotlight_type(message: Message, state: FSMContext, user_id: int) -> None:
    """Переходит к следующему типу светильника."""
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    selected = set(data.get("selected_spotlight_types", set()))
    order = ["builtin", "surface", "pendant"]
    
    for spot_type in order:
        if spot_type in selected and data.get(f"spotlights_{spot_type}") is None:
            await _ask_spotlight_count(message, state, user_id, spot_type)
            return
    
    # Все типы обработаны
    await state.update_data(editing_mode=False)
    if editing_mode:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _process_next_lighting(message, state, user_id)


async def _ask_spotlight_count(message: Message, state: FSMContext, user_id: int, spot_type: str) -> None:
    """Запрашивает количество светильников определённого типа."""
    questions = {
        "builtin": SPOTLIGHTS_BUILTIN_QUESTION,
        "surface": SPOTLIGHTS_SURFACE_QUESTION,
        "pendant": SPOTLIGHTS_PENDANT_QUESTION,
    }
    states = {
        "builtin": CalculationStates.entering_spotlights_builtin,
        "surface": CalculationStates.entering_spotlights_surface,
        "pendant": CalculationStates.entering_spotlights_pendant,
    }
    
    question = questions[spot_type]
    await message.answer(question, reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(states[spot_type])
    chat_logger.log_message(user_id=user_id, username="БОТ", message=question, is_bot=True)


async def _process_spotlight_count(message: Message, state: FSMContext, count: int, spot_type: str) -> None:
    """Обрабатывает количество светильников."""
    names = {"builtin": "Встроенные", "surface": "Накладные", "pendant": "Подвесные"}
    await state.update_data(**{f"spotlights_{spot_type}": count})
    
    response = SPOTLIGHTS_ACCEPTED.format(spot_type=names[spot_type], count=count)
    await message.answer(response, parse_mode=ParseMode.HTML)
    await _process_next_spotlight_type(message, state, message.from_user.id)


@router.message(CalculationStates.entering_spotlights_builtin)
@router.message(CalculationStates.entering_spotlights_surface)
@router.message(CalculationStates.entering_spotlights_pendant)
async def process_spotlight_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода количества светильников."""
    if not message.text:
        await message.answer(SPOTLIGHTS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    count = parse_int(message.text)
    if count is None or count < 0:
        await message.answer(SPOTLIGHTS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    current_state = await state.get_state()
    spot_type = current_state.split("_")[-1]  # builtin/surface/pendant
    await _process_spotlight_count(message, state, count, spot_type)


# ============================================
# ТРЕКИ - ВЫБОР ТИПОВ
# ============================================


async def _ask_track_types(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает выбор типов треков."""
    await state.update_data(selected_track_types=set(), previous_state=CalculationStates.choosing_spotlight_types)
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "tracks_all.jpg")
    
    data = await state.get_data()
    selected = data.get("selected_lighting", set())
    total_steps = calculate_total_steps(selected, False)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected, "tracks")
    
    await message.answer(
        with_progress(TRACK_TYPES_QUESTION, step, total_steps),
        reply_markup=get_track_types_keyboard(set()),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(CalculationStates.choosing_track_types)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=TRACK_TYPES_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_track_types, F.data.startswith("toggle_track_"))
async def toggle_track_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Переключает выбор типа трека."""
    await safe_answer_callback(callback)
    
    track_type = callback.data.replace("toggle_track_", "")
    data = await state.get_data()
    selected = set(data.get("selected_track_types", set()))
    
    if track_type in selected:
        selected.discard(track_type)
    else:
        selected.add(track_type)
    
    await state.update_data(selected_track_types=selected)
    
    selected_lighting = data.get("selected_lighting", set())
    total_steps = calculate_total_steps(selected_lighting, False)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected_lighting, "tracks")
    
    await callback.message.edit_text(
        with_progress(TRACK_TYPES_QUESTION, step, total_steps),
        reply_markup=get_track_types_keyboard(selected),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(CalculationStates.choosing_track_types, F.data == "tracks_done")
async def tracks_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершает выбор типов треков."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    selected = set(data.get("selected_track_types", set()))
    
    if not selected:
        await state.update_data(track_surface_length=0, track_builtin_length=0, editing_mode=False)
        await callback.message.answer(NO_TRACKS, parse_mode=ParseMode.HTML)
        if editing_mode:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _process_next_lighting(callback.message, state, callback.from_user.id)
        return
    
    await _process_next_track_type(callback.message, state, callback.from_user.id)


@router.callback_query(CalculationStates.choosing_track_types, F.data == "tracks_skip")
async def tracks_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропускает треки."""
    await safe_answer_callback(callback)
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    await state.update_data(track_surface_length=0, track_builtin_length=0, editing_mode=False)
    await callback.message.answer(NO_TRACKS, parse_mode=ParseMode.HTML)
    if editing_mode:
        await _show_result_after_edit(callback.message, state, callback.from_user)
    else:
        await _process_next_lighting(callback.message, state, callback.from_user.id)


async def _process_next_track_type(message: Message, state: FSMContext, user_id: int) -> None:
    """Переходит к следующему типу трека."""
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    selected = set(data.get("selected_track_types", set()))
    order = ["surface", "builtin"]
    
    for track_type in order:
        if track_type in selected and data.get(f"track_{track_type}_length") is None:
            await _ask_track_length(message, state, user_id, track_type)
            return
    
    # Все типы обработаны
    await state.update_data(editing_mode=False)
    if editing_mode:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _process_next_lighting(message, state, user_id)


async def _ask_track_length(message: Message, state: FSMContext, user_id: int, track_type: str) -> None:
    """Запрашивает длину треков определённого типа."""
    questions = {
        "surface": TRACK_SURFACE_LENGTH_QUESTION,
        "builtin": TRACK_BUILTIN_LENGTH_QUESTION,
    }
    states = {
        "surface": CalculationStates.entering_track_surface_length,
        "builtin": CalculationStates.entering_track_builtin_length,
    }
    
    question = questions[track_type]
    await message.answer(question, reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(states[track_type])
    chat_logger.log_message(user_id=user_id, username="БОТ", message=question, is_bot=True)


async def _process_track_length(message: Message, state: FSMContext, length: float, track_type: str) -> None:
    """Обрабатывает длину треков."""
    names = {"surface": "Накладные треки", "builtin": "Встроенные треки"}
    await state.update_data(**{f"track_{track_type}_length": length})
    
    response = TRACK_LENGTH_ACCEPTED.format(track_type=names[track_type], length=length)
    await message.answer(response, parse_mode=ParseMode.HTML)
    await _process_next_track_type(message, state, message.from_user.id)


@router.message(CalculationStates.entering_track_surface_length)
@router.message(CalculationStates.entering_track_builtin_length)
async def process_track_length_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины треков."""
    if not message.text:
        await message.answer(TRACK_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    length = parse_float(message.text)
    if length is None or length < 0:
        await message.answer(TRACK_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    current_state = await state.get_state()
    track_type = "surface" if "surface" in current_state else "builtin"
    await _process_track_length(message, state, length, track_type)


# ============================================
# СВЕТОВЫЕ ЛИНИИ
# ============================================


async def _ask_light_lines(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает длину световых линий."""
    data = await state.get_data()
    previous = CalculationStates.choosing_track_types
    await state.update_data(previous_state=previous)
    
    selected = data.get("selected_lighting")
    all_steps = data.get("all_lighting_steps", False)
    total_steps = calculate_total_steps(selected, all_steps)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected if not all_steps else None, "light_lines")
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "light_lines.jpg", [])
    
    await message.answer(with_progress(LIGHT_LINES_QUESTION, step, total_steps), reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_light_lines)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=LIGHT_LINES_QUESTION, is_bot=True)


@router.message(CalculationStates.entering_light_lines)
async def process_light_lines(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины световых линий."""
    if not message.text:
        await message.answer(LIGHT_LINES_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    length = parse_float(message.text)
    if length is None or length < 0:
        await message.answer(LIGHT_LINES_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(light_lines=length, editing_mode=False)
    
    username = get_user_display_name(message.from_user)
    chat_logger.log_message(user_id=message.from_user.id, username=username, message=f"Световые линии: {length} пог.м", is_bot=False)

    response = LIGHT_LINES_ACCEPTED.format(length=length)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=message.from_user.id, username="БОТ", message=response, is_bot=True)

    all_steps = data.get("all_lighting_steps", False)
    
    if editing_mode:
        await _show_result_after_edit(message, state, message.from_user)
    elif all_steps:
        await _ask_chandeliers(message, state, message.from_user.id)
    else:
        await _process_next_lighting(message, state, message.from_user.id)


# ============================================
# ОСВЕЩЕНИЕ - ЛЮСТРЫ
# ============================================


async def _ask_chandeliers(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает количество люстр."""
    data = await state.get_data()
    await state.update_data(previous_state=CalculationStates.entering_light_lines)
    
    selected = data.get("selected_lighting")
    all_steps = data.get("all_lighting_steps", False)
    total_steps = calculate_total_steps(selected, all_steps)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected if not all_steps else None, "chandeliers")
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "chandeliers.jpg")
    await message.answer(with_progress(CHANDELIERS_QUESTION, step, total_steps), reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_chandeliers)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=CHANDELIERS_QUESTION, is_bot=True)


@router.message(CalculationStates.entering_chandeliers)
async def process_chandeliers_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода люстр."""
    if not message.text:
        await message.answer(CHANDELIERS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    count = parse_int(message.text)
    if count is None:
        await message.answer(CHANDELIERS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    if not validate_range(count, 0, settings.max_count):
        await message.answer(
            get_count_validation_error(settings.max_count),
            parse_mode=ParseMode.HTML
        )
        return

    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Люстры: {count} шт",
        is_bot=False,
    )

    await _process_chandeliers(message, state, count, message.from_user)


async def _process_chandeliers(
    message: Message, state: FSMContext, count: int, user: User
) -> None:
    """Сохраняет количество люстр и переходит к вопросу о чистовых работах."""
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(chandeliers=count, editing_mode=False)

    response = CHANDELIERS_ACCEPTED.format(count=count)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user.id, username="БОТ", message=response, is_bot=True)

    if editing_mode:
        await _show_result_after_edit(message, state, user)
    else:
        await _ask_wall_finish(message, state, user.id)


# ============================================
# ЧИСТОВЫЕ РАБОТЫ СТЕН
# ============================================


async def _ask_wall_finish(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает информацию о чистовых работах стен."""
    data = await state.get_data()
    await state.update_data(previous_state=CalculationStates.entering_chandeliers)
    
    selected = data.get("selected_lighting")
    all_steps = data.get("all_lighting_steps", False)
    total_steps = calculate_total_steps(selected, all_steps)
    step = get_dynamic_step(STEP_LIGHTING_TYPES, selected if not all_steps else None, "wall_finish")
    
    await message.answer(with_progress(WALL_FINISH_QUESTION, step, total_steps), reply_markup=get_wall_finish_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_wall_finish)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=WALL_FINISH_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_wall_finish, F.data.startswith("wall_"))
async def process_wall_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора чистовых работ стен."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    wall_finish = callback.data == "wall_yes"
    answer_text = "Да" if wall_finish else "Нет"
    
    await state.update_data(wall_finish=wall_finish, editing_mode=False)
    
    username = get_user_display_name(callback.from_user)
    chat_logger.log_message(user_id=callback.from_user.id, username=username, message=f"Чистовые работы стен: {answer_text}", is_bot=False)
    
    response = WALL_FINISH_ACCEPTED.format(answer=answer_text)
    await callback.message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=callback.from_user.id, username="БОТ", message=response, is_bot=True)
    
    if editing_mode:
        await _show_result_after_edit(callback.message, state, callback.from_user)
    else:
        await _show_result(callback.message, state, callback.from_user)


# ============================================
# РЕЗУЛЬТАТ И ОТПРАВКА АДМИНУ
# ============================================


def _format_result_info(calculation: CalculationData) -> tuple[str, str, str]:
    """Формирует информацию о расчёте для отображения."""
    area_note = ""
    if calculation.area < settings.min_area_for_calculation:
        area_note = f"• Расчёт от минимальной площади: {calculation.area_for_calculation} м²\n"

    profile_name = get_profile_name(calculation.profile_type)
    if calculation.profile_type == "insert":
        profile_info = f"• Профиль: {profile_name}\n"
    else:
        perimeter = calculation.area * settings.perimeter_coefficient
        profile_info = f"• Профиль: {profile_name} — {perimeter:.1f} пог.м\n"

    lighting_info = ""
    total_spotlights = calculation.spotlights_builtin + calculation.spotlights_surface + calculation.spotlights_pendant
    if total_spotlights > 0:
        lighting_info += f"• Точечные светильники: {total_spotlights} шт\n"
        details = []
        if calculation.spotlights_builtin > 0:
            details.append(f"  - Встроенные ({calculation.spotlights_builtin} шт)")
        if calculation.spotlights_surface > 0:
            details.append(f"  - Накладные ({calculation.spotlights_surface} шт)")
        if calculation.spotlights_pendant > 0:
            details.append(f"  - Подвесные ({calculation.spotlights_pendant} шт)")
        if details:
            lighting_info += "\n".join(details) + "\n"
    
    total_tracks = calculation.track_surface_length + calculation.track_builtin_length
    if total_tracks > 0:
        lighting_info += f"• Треки: {total_tracks} пог.м\n"
        details = []
        if calculation.track_surface_length > 0:
            details.append(f"  - Накладные ({calculation.track_surface_length} пог.м)")
        if calculation.track_builtin_length > 0:
            details.append(f"  - Встроенные ({calculation.track_builtin_length} пог.м)")
        if details:
            lighting_info += "\n".join(details) + "\n"
    
    if calculation.light_lines > 0:
        lighting_info += f"• Световые линии: {calculation.light_lines} пог.м\n"
    if calculation.chandeliers > 0:
        lighting_info += f"• Люстры: {calculation.chandeliers} шт\n"

    return area_note, profile_info, lighting_info


async def _show_result(message: Message, state: FSMContext, user: User) -> None:
    """Показывает результат расчёта и отправляет админу."""
    # Получение данных
    data = await state.get_data()
    
    # Проверка обязательных полей
    if "area" not in data or "profile_type" not in data:
        await message.answer(
            "❌ Ошибка: не все обязательные параметры заполнены. Пожалуйста, начните расчёт заново.",
            parse_mode=ParseMode.HTML
        )
        return

    # Расчёт
    calculation = calculate_total(data)

    # Формирование сообщения для пользователя
    area_note, profile_info, lighting_info = _format_result_info(calculation)

    result_text = RESULT_MESSAGE.format(
        area=calculation.area,
        area_note=area_note,
        cornice_info=profile_info,  # profile_info содержит информацию о профиле с периметром
        lighting_info=lighting_info,
        total=calculation.total_cost,
    )

    await message.answer(result_text, reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML)

    await state.set_state(CalculationStates.showing_result)

    chat_logger.log_message(user_id=user.id, username="БОТ", message=result_text, is_bot=True)

    # Отправка уведомления админу
    await _notify_admin(message.bot, user, calculation, data)


def _format_admin_details(calculation: CalculationData) -> str:
    """Форматирует детализацию расчёта для админа.
    
    Args:
        calculation: Данные расчёта
        
    Returns:
        Отформатированная детализация
    """
    details = format_ceiling_details(
        calculation.area_for_calculation,
        calculation.ceiling_cost,
        settings.ceiling_base_price,
    )

    if calculation.profile_cost > 0:
        perimeter = calculation.area * settings.perimeter_coefficient
        profile_name = get_profile_name(calculation.profile_type)
        details += format_profile_details(
            profile_name, perimeter, calculation.profile_cost
        )

    if calculation.cornice_cost > 0:
        cornice_name = get_cornice_name(calculation.cornice_type)
        if cornice_name:
            details += format_cornice_details(
                cornice_name, calculation.cornice_length, calculation.cornice_cost
            )

    if calculation.spotlights_cost > 0:
        details += format_spotlights_details(
            calculation.spotlights_builtin,
            calculation.spotlights_surface,
            calculation.spotlights_pendant,
            calculation.spotlights_cost,
            {
                "builtin": settings.spotlight_builtin_price,
                "surface": settings.spotlight_surface_price,
                "pendant": settings.spotlight_pendant_price,
            },
        )

    if calculation.track_cost > 0:
        details += format_track_details(
            calculation.track_surface_length,
            calculation.track_builtin_length,
            calculation.track_cost,
            {
                "surface": settings.track_surface_price,
                "builtin": settings.track_built_in_price,
            },
        )

    if calculation.light_lines_cost > 0:
        details += format_light_lines_details(
            calculation.light_lines, calculation.light_lines_cost, settings.light_lines_price
        )

    if calculation.chandeliers_cost > 0:
        details += format_chandeliers_details(
            calculation.chandeliers,
            calculation.chandeliers_cost,
            settings.chandelier_price,
        )

    return details


async def _send_notification(bot: Bot, chat_id: int, report: str) -> None:
    """Отправляет уведомление в чат (группу или пользователю).
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата (группы или пользователя)
        report: Текст отчёта
    """
    try:
        await bot.send_message(chat_id=chat_id, text=report, parse_mode=ParseMode.HTML)
    except Exception as e:
        error_msg = str(e).lower()
        if "chat not found" not in error_msg and "bot was blocked" not in error_msg:
            logger.warning(f"Не удалось отправить уведомление в чат {chat_id}: {e}")


async def _notify_admin(
    bot: Bot, user: User, calculation: CalculationData, data: dict, is_update: bool = False
) -> None:
    """Отправляет уведомление о завершении расчёта в канал, группу и/или менеджерам."""
    if not bot:
        return

    try:
        username = f"@{user.username}" if user.username else "нет username"
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        title = "ИЗМЕНЁННЫЙ РАСЧЁТ ✏️" if is_update else "НОВЫЙ РАСЧЁТ"

        area_note, profile_info, lighting_info = _format_result_info(calculation)
        details = _format_admin_details(calculation)

        wall_status = "✅" if calculation.wall_finish else "❌"
        
        admin_report = ADMIN_REPORT.format(
            title=title,
            username=username,
            full_name=user.full_name,
            date=date,
            area=calculation.area,
            area_note=area_note,
            profile_info=profile_info,
            lighting_info=lighting_info,
            total=calculation.total_cost,
            details=details,
            wall_finish_status=wall_status,
        )

        # Отправка в канал (если настроен)
        if settings.channel_chat_id:
            await _send_notification(bot, int(settings.channel_chat_id), admin_report)

        # Отправка в группу (если настроена)
        if settings.group_chat_id:
            await _send_notification(bot, int(settings.group_chat_id), admin_report)

        # Отправка каждому менеджеру (если настроены)
        for admin_id in settings.admin_ids_list:
            await _send_notification(bot, admin_id, admin_report)

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")


# ============================================
# РЕДАКТИРОВАНИЕ ПАРАМЕТРОВ
# ============================================


async def _show_result_after_edit(message: Message, state: FSMContext, user: User) -> None:
    """Показывает результат расчёта после редактирования и уведомляет менеджеров."""
    data = await state.get_data()
    
    # Проверка обязательных полей
    if "area" not in data or "profile_type" not in data:
        await message.answer(
            "❌ Ошибка: не все обязательные параметры заполнены. Пожалуйста, начните расчёт заново.",
            parse_mode=ParseMode.HTML
        )
        return
    
    calculation = calculate_total(data)
    area_note, profile_info, lighting_info = _format_result_info(calculation)
    
    result_text = RESULT_MESSAGE.format(
        area=calculation.area,
        area_note=area_note,
        cornice_info=profile_info,
        lighting_info=lighting_info,
        total=calculation.total_cost,
    )
    
    await message.answer(result_text, reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.showing_result)
    
    chat_logger.log_message(user_id=user.id, username="БОТ", message="📊 Обновлённый результат", is_bot=True)
    
    # Уведомление менеджеров об изменённом расчёте
    await _notify_admin(message.bot, user, calculation, data, is_update=True)


@router.callback_query(F.data == "edit_params")
async def show_edit_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Показ меню редактирования параметров."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    await callback.message.answer(
        EDIT_PARAMS_MESSAGE,
        reply_markup=get_edit_params_keyboard(data),
        parse_mode=ParseMode.HTML
    )
    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=EDIT_PARAMS_MESSAGE, is_bot=True
    )


@router.callback_query(F.data == "back_to_result")
async def back_to_result(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат к результату расчёта из меню редактирования."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    user = callback.from_user
    
    # Проверка обязательных полей
    if "area" not in data or "profile_type" not in data:
        await callback.message.answer(
            "❌ Ошибка: не все обязательные параметры заполнены. Пожалуйста, начните расчёт заново.",
            parse_mode=ParseMode.HTML
        )
        return
    
    calculation = calculate_total(data)
    area_note, profile_info, lighting_info = _format_result_info(calculation)
    
    result_text = RESULT_MESSAGE.format(
        area=calculation.area,
        area_note=area_note,
        cornice_info=profile_info,
        lighting_info=lighting_info,
        total=calculation.total_cost,
    )
    
    await callback.message.answer(result_text, reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.showing_result)
    
    chat_logger.log_message(user_id=user.id, username="БОТ", message="📊 Результат расчёта", is_bot=True)


@router.callback_query(F.data == "edit_area")
async def edit_area(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование площади."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await ask_area(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование профиля."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_profile(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_cornice")
async def edit_cornice(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование карниза."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_cornice_type(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_spotlights")
async def edit_spotlights(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование светильников."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True, selected_spotlight_types=None)
    await _ask_spotlight_types(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_chandeliers")
async def edit_chandeliers(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование количества люстр."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_chandeliers(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_tracks")
async def edit_tracks(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование треков."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True, selected_track_types=None)
    await _ask_track_types(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_light_lines")
async def edit_light_lines(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование световых линий."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_light_lines(callback.message, state, callback.from_user.id)


@router.callback_query(F.data == "edit_wall_finish")
async def edit_wall_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование чистовых работ стен."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_wall_finish(callback.message, state, callback.from_user.id)


# ============================================
# ЗАКАЗ ЗАМЕРА
# ============================================


@router.callback_query(F.data == "order_measurement")
async def start_measurement_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало заказа бесплатного замера."""
    await safe_answer_callback(callback)
    
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.showing_result)
    
    await _ask_name(callback.message, state, callback.from_user.id)


async def _ask_name(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает имя заказчика."""
    await state.update_data(previous_state=CalculationStates.showing_result)
    await message.answer(NAME_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_name)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=NAME_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_name)
async def process_name_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода имени."""
    if not message.text:
        await message.answer(NAME_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer(NAME_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    await state.update_data(customer_name=name)

    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Имя: {name}",
        is_bot=False,
    )

    response = NAME_ACCEPTED.format(name=name)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=response, is_bot=True
    )

    # Переход к вопросу о телефоне
    await _ask_phone(message, state, message.from_user.id)


async def _ask_phone(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает номер телефона."""
    await state.update_data(previous_state=CalculationStates.entering_name)
    await message.answer(PHONE_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_phone)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=PHONE_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_phone)
async def process_phone_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода номера телефона."""
    if not message.text:
        await message.answer(PHONE_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    phone = message.text.strip()
    
    if not validate_phone(phone):
        await message.answer(PHONE_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    normalized_phone = normalize_phone(phone)
    await state.update_data(phone=normalized_phone)

    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Телефон: {normalized_phone}",
        is_bot=False,
    )

    response = PHONE_ACCEPTED.format(phone=normalized_phone)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=response, is_bot=True
    )

    # Переход к вопросу об адресе
    await _ask_address(message, state, message.from_user.id)


async def _ask_address(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает адрес объекта."""
    await state.update_data(previous_state=CalculationStates.entering_phone)
    await message.answer(ADDRESS_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_address)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=ADDRESS_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_address)
async def process_address_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода адреса."""
    if not message.text:
        await message.answer(ADDRESS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    address = message.text.strip()
    
    if len(address) < 5:
        await message.answer(ADDRESS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    await state.update_data(address=address)

    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Адрес: {address}",
        is_bot=False,
    )

    response = ADDRESS_ACCEPTED.format(address=address)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=response, is_bot=True
    )

    # Отправка благодарности
    await message.answer(MEASUREMENT_THANK_YOU, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=MEASUREMENT_THANK_YOU, is_bot=True
    )

    # Отправка уведомления менеджеру
    await _notify_manager_about_measurement(message.bot, message.from_user, state)

    # Возврат к результату
    await state.set_state(CalculationStates.showing_result)


async def _notify_manager_about_measurement(bot: Bot, user: User, state: FSMContext) -> None:
    """Отправляет уведомление о заказе замера в канал, группу и/или менеджерам."""
    if not bot:
        return

    try:
        data = await state.get_data()
        customer_name = data.get("customer_name", "")
        phone = data.get("phone", "")
        address = data.get("address", "")

        if not customer_name or not phone or not address:
            logger.warning("Не удалось отправить уведомление о замере: отсутствуют данные")
            return

        username = f"@{user.username}" if user.username else "нет username"
        date = datetime.now().strftime("%d.%m.%Y %H:%M")

        measurement_report = MEASUREMENT_REPORT.format(
            username=username,
            full_name=user.full_name,
            customer_name=customer_name,
            phone=phone,
            address=address,
            date=date,
        )

        # Отправка в канал (если настроен)
        if settings.channel_chat_id:
            await _send_notification(bot, int(settings.channel_chat_id), measurement_report)

        # Отправка в группу (если настроена)
        if settings.group_chat_id:
            await _send_notification(bot, int(settings.group_chat_id), measurement_report)

        # Отправка каждому менеджеру (если настроены)
        for admin_id in settings.admin_ids_list:
            await _send_notification(bot, admin_id, measurement_report)

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о замере: {e}")
