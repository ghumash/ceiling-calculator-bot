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
    get_track_type_keyboard,
    get_wall_finish_keyboard,
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
    SPOTLIGHTS_QUESTION,
    SPOTLIGHTS_ACCEPTED,
    SPOTLIGHTS_INVALID_INPUT,
    TRACK_TYPE_QUESTION,
    TRACK_TYPE_ACCEPTED,
    NO_TRACKS,
    TRACK_LENGTH_QUESTION,
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
    get_track_type_name,
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

# Номера шагов для прогресс-бара
STEP_AREA = 1
STEP_PROFILE = 2
STEP_CORNICE_TYPE = 3
STEP_CORNICE_LENGTH = 4
STEP_SPOTLIGHTS = 5
STEP_TRACK_TYPE = 6
STEP_TRACK_LENGTH = 7
STEP_LIGHT_LINES = 8
STEP_CHANDELIERS = 9
STEP_WALL_FINISH = 10
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
    """Возврат из световых линий к трекам или типу треков."""
    if data.get("track_type"):
        await _ask_track_length(callback.message, state, user_id)
    else:
        await _ask_track_type(callback.message, state, user_id)


@router.callback_query(F.data == "skip_zero")
async def skip_with_zero(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Не нужно' — устанавливает 0."""
    await safe_answer_callback(callback)
    
    current_state = await state.get_state()
    user_id = callback.from_user.id
    
    if current_state == CalculationStates.entering_spotlights:
        await _process_spotlights(callback.message, state, 0, user_id)
    elif current_state == CalculationStates.entering_light_lines:
        data = await state.get_data()
        editing_mode = data.get("editing_mode", False)
        await state.update_data(light_lines=0, editing_mode=False)
        await callback.message.answer("✅ <b>Световые линии:</b> не требуются", parse_mode=ParseMode.HTML)
        if editing_mode and data.get("wall_finish") is not None:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _ask_chandeliers(callback.message, state, user_id)
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
        CalculationStates.entering_spotlights: lambda cb, st, uid: _go_back_to_spotlights(cb, st, uid, data),
        CalculationStates.choosing_track_type: lambda cb, st, uid: _ask_spotlights(cb.message, st, uid),
        CalculationStates.entering_track_length: lambda cb, st, uid: _ask_track_type(cb.message, st, uid),
        CalculationStates.entering_light_lines: lambda cb, st, uid: _go_back_from_light_lines(cb, st, uid, data),
        CalculationStates.entering_chandeliers: lambda cb, st, uid: _ask_light_lines(cb.message, st, uid),
        CalculationStates.choosing_wall_finish: lambda cb, st, uid: _ask_chandeliers(cb.message, st, uid),
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

    if editing_mode and data.get("profile_type"):
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

    if editing_mode and data.get("spotlights") is not None:
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
        
        if editing_mode and data.get("spotlights") is not None:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _ask_spotlights(callback.message, state, callback.from_user.id)
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

    if editing_mode and data.get("spotlights") is not None:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_spotlights(message, state, message.from_user.id)


# ============================================
# ОСВЕЩЕНИЕ - СВЕТИЛЬНИКИ
# ============================================


async def _ask_spotlights(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает количество закладных под точечные светильники."""
    data = await state.get_data()
    previous_state = _get_previous_lighting_state(data)
    await state.update_data(previous_state=previous_state)
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "spotlights.jpg")
    await message.answer(with_progress(SPOTLIGHTS_QUESTION, STEP_SPOTLIGHTS), reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_spotlights)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=SPOTLIGHTS_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_spotlights)
async def process_spotlights_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода светильников."""
    if not message.text:
        await message.answer(SPOTLIGHTS_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    count = parse_int(message.text)
    if count is None:
        await message.answer(SPOTLIGHTS_INVALID_INPUT, parse_mode=ParseMode.HTML)
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
        message=f"Светильники: {count} шт",
        is_bot=False,
    )

    await _process_spotlights(message, state, count, message.from_user.id)


async def _process_spotlights(
    message: Message, state: FSMContext, count: int, user_id: int
) -> None:
    """Сохраняет количество светильников и переходит к трекам или результату."""
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(spotlights=count, editing_mode=False)

    response = SPOTLIGHTS_ACCEPTED.format(count=count)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=response, is_bot=True)

    if editing_mode and data.get("wall_finish") is not None:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_track_type(message, state, user_id)


# ============================================
# ТРЕКИ
# ============================================


async def _ask_track_type(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает тип трековых линий."""
    await state.update_data(previous_state=CalculationStates.entering_spotlights)
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "tracks_all.jpg", [])
    
    await message.answer(with_progress(TRACK_TYPE_QUESTION, STEP_TRACK_TYPE), reply_markup=get_track_type_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_track_type)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=TRACK_TYPE_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_track_type, F.data.startswith("track_"))
async def process_track_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора типа треков."""
    await safe_answer_callback(callback)
    
    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    track_type = callback.data.replace("track_", "")
    
    if track_type == "none":
        await state.update_data(track_type=None, track_length=0, editing_mode=False)
        await callback.message.answer(NO_TRACKS, parse_mode=ParseMode.HTML)
        chat_logger.log_message(user_id=callback.from_user.id, username="БОТ", message=NO_TRACKS, is_bot=True)
        
        if editing_mode and data.get("wall_finish") is not None:
            await _show_result_after_edit(callback.message, state, callback.from_user)
        else:
            await _ask_light_lines(callback.message, state, callback.from_user.id)
        return
    
    track_name = get_track_type_name(track_type)
    await state.update_data(track_type=track_type)
    
    username = get_user_display_name(callback.from_user)
    chat_logger.log_message(user_id=callback.from_user.id, username=username, message=f"Тип треков: {track_name}", is_bot=False)
    
    response = TRACK_TYPE_ACCEPTED.format(track_type=track_name)
    await callback.message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=callback.from_user.id, username="БОТ", message=response, is_bot=True)
    
    await _ask_track_length(callback.message, state, callback.from_user.id)


async def _ask_track_length(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает длину треков."""
    await state.update_data(previous_state=CalculationStates.choosing_track_type)
    await message.answer(with_progress(TRACK_LENGTH_QUESTION, STEP_TRACK_LENGTH), reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_track_length)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=TRACK_LENGTH_QUESTION, is_bot=True)


@router.message(CalculationStates.entering_track_length)
async def process_track_length(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины треков."""
    if not message.text:
        await message.answer(TRACK_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    length = parse_float(message.text)
    if length is None or length <= 0:
        await message.answer(TRACK_INVALID_INPUT, parse_mode=ParseMode.HTML)
        return

    data = await state.get_data()
    editing_mode = data.get("editing_mode", False)
    
    await state.update_data(track_length=length, editing_mode=False)
    
    username = get_user_display_name(message.from_user)
    chat_logger.log_message(user_id=message.from_user.id, username=username, message=f"Длина треков: {length} м", is_bot=False)

    response = TRACK_LENGTH_ACCEPTED.format(length=length)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=message.from_user.id, username="БОТ", message=response, is_bot=True)

    if editing_mode and data.get("wall_finish") is not None:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_light_lines(message, state, message.from_user.id)


# ============================================
# СВЕТОВЫЕ ЛИНИИ
# ============================================


async def _ask_light_lines(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает длину световых линий."""
    data = await state.get_data()
    track_type = data.get("track_type")
    previous = CalculationStates.entering_track_length if track_type else CalculationStates.choosing_track_type
    await state.update_data(previous_state=previous)
    
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "light_lines.jpg", [])
    
    await message.answer(with_progress(LIGHT_LINES_QUESTION, STEP_LIGHT_LINES), reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
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
    chat_logger.log_message(user_id=message.from_user.id, username=username, message=f"Световые линии: {length} м", is_bot=False)

    response = LIGHT_LINES_ACCEPTED.format(length=length)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=message.from_user.id, username="БОТ", message=response, is_bot=True)

    if editing_mode and data.get("wall_finish") is not None:
        await _show_result_after_edit(message, state, message.from_user)
    else:
        await _ask_chandeliers(message, state, message.from_user.id)


# ============================================
# ОСВЕЩЕНИЕ - ЛЮСТРЫ
# ============================================


async def _ask_chandeliers(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает количество люстр."""
    await state.update_data(previous_state=CalculationStates.entering_light_lines)
    lighting_path = Path(settings.lighting_dir)
    await send_image_if_exists(message, lighting_path / "chandeliers.jpg")
    await message.answer(with_progress(CHANDELIERS_QUESTION, STEP_CHANDELIERS), reply_markup=get_skip_row_keyboard(), parse_mode=ParseMode.HTML)
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

    if editing_mode and data.get("wall_finish") is not None:
        await _show_result_after_edit(message, state, user)
    else:
        await _ask_wall_finish(message, state, user.id)


# ============================================
# ЧИСТОВЫЕ РАБОТЫ СТЕН
# ============================================


async def _ask_wall_finish(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает информацию о чистовых работах стен."""
    await state.update_data(previous_state=CalculationStates.entering_chandeliers)
    await message.answer(with_progress(WALL_FINISH_QUESTION, STEP_WALL_FINISH), reply_markup=get_wall_finish_keyboard(), parse_mode=ParseMode.HTML)
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
    if calculation.spotlights > 0:
        lighting_info += f"• Точечные светильники: {calculation.spotlights} шт\n"
    if calculation.track_type and calculation.track_length > 0:
        track_name = get_track_type_name(calculation.track_type)
        lighting_info += f"• Треки ({track_name}): {calculation.track_length} м\n"
    if calculation.light_lines > 0:
        lighting_info += f"• Световые линии: {calculation.light_lines} м\n"
    if calculation.chandeliers > 0:
        lighting_info += f"• Люстры: {calculation.chandeliers} шт\n"

    return area_note, profile_info, lighting_info


async def _show_result(message: Message, state: FSMContext, user: User) -> None:
    """Показывает результат расчёта и отправляет админу."""
    # Получение данных
    data = await state.get_data()

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
            calculation.spotlights,
            calculation.spotlights_cost,
            settings.spotlight_price,
        )

    if calculation.track_cost > 0:
        track_name = get_track_type_name(calculation.track_type)
        track_price = settings.track_surface_price if calculation.track_type == "surface" else settings.track_built_in_price
        details += format_track_details(
            track_name, calculation.track_length, calculation.track_cost, track_price
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
    """Редактирование количества светильников."""
    await safe_answer_callback(callback)
    await state.update_data(editing_mode=True)
    await _ask_spotlights(callback.message, state, callback.from_user.id)


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
    await state.update_data(editing_mode=True)
    await _ask_track_type(callback.message, state, callback.from_user.id)


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
