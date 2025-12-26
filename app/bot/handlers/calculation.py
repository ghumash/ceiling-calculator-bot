"""Обработчик FSM диалога расчёта."""

import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, User

from app.bot.states import CalculationStates
from app.bot.keyboards.inline import (
    get_profile_keyboard,
    get_cornice_keyboard,
    get_result_keyboard,
    get_back_keyboard,
    get_contact_method_keyboard,
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
    CORNICE_VALIDATION_ERROR,
    CORNICE_INVALID_INPUT,
    SPOTLIGHTS_QUESTION,
    SPOTLIGHTS_ACCEPTED,
    SPOTLIGHTS_INVALID_INPUT,
    CHANDELIERS_QUESTION,
    CHANDELIERS_ACCEPTED,
    CHANDELIERS_INVALID_INPUT,
    COUNT_VALIDATION_ERROR,
    RESULT_MESSAGE,
    RESULT_DETAILS_CEILING,
    RESULT_DETAILS_PROFILE,
    RESULT_DETAILS_CORNICE,
    RESULT_DETAILS_SPOTLIGHTS,
    RESULT_DETAILS_CHANDELIERS,
    ADMIN_REPORT,
    WELCOME_MESSAGE,
    get_profile_name,
    get_cornice_name,
)
from app.services.chat_logger import chat_logger
from app.services.calculator import calculate_total
from app.schemas.calculation import CalculationData
from app.core.config import settings

logger = logging.getLogger(__name__)
router = Router()


# ============================================
# ВОЗВРАТ НАЗАД
# ============================================


@router.callback_query(F.data == "go_back")
async def go_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата на предыдущий шаг."""
    await callback.answer()
    
    data = await state.get_data()
    current_state = await state.get_state()
    user_id = callback.from_user.id
    
    # Очищаем данные текущего шага при возврате
    if current_state == CalculationStates.waiting_for_area:
        # Возврат к выбору способа связи
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
        
    elif current_state == CalculationStates.choosing_profile:
        # Возврат к площади - удаляем профиль из данных
        await state.update_data(profile_type=None, previous_state=CalculationStates.choosing_contact_method)
        await ask_area(callback.message, state, user_id)
        
    elif current_state == CalculationStates.entering_cornice_length:
        # Возврат к профилю - удаляем данные карнизов
        await state.update_data(cornice_length=None, cornice_type=None, previous_state=CalculationStates.waiting_for_area)
        await _ask_profile(callback.message, state, user_id)
        
    elif current_state == CalculationStates.choosing_cornice_type:
        # Возврат к длине карнизов - удаляем тип карниза
        await state.update_data(cornice_type=None, previous_state=CalculationStates.choosing_profile)
        await _ask_cornice_length(callback.message, state, user_id)
        
    elif current_state == CalculationStates.entering_spotlights:
        # Возврат к карнизам или профилю
        await state.update_data(spotlights=None, previous_state=None)
        profile_type = data.get("profile_type")
        if profile_type == "insert" or data.get("cornice_length", 0) == 0:
            # Профиль "insert" или нет карнизов - возврат к профилю
            await state.update_data(previous_state=CalculationStates.waiting_for_area)
            await _ask_profile(callback.message, state, user_id)
        else:
            # Есть карнизы - возврат к типу карниза
            await state.update_data(previous_state=CalculationStates.entering_cornice_length)
            await _ask_cornice_type(callback.message, state, user_id)
        
    elif current_state == CalculationStates.entering_chandeliers:
        # Возврат к светильникам - удаляем люстры
        await state.update_data(chandeliers=None, previous_state=None)
        profile_type = data.get("profile_type")
        if profile_type == "insert" or data.get("cornice_length", 0) == 0:
            previous_state = CalculationStates.choosing_profile
        else:
            previous_state = CalculationStates.choosing_cornice_type
        await state.update_data(previous_state=previous_state)
        await _ask_spotlights(callback.message, state, user_id)
    
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
    await message.answer(AREA_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.waiting_for_area)

    chat_logger.log_message(user_id=user_id, username="БОТ", message=AREA_QUESTION, is_bot=True)


@router.message(CalculationStates.waiting_for_area)
async def process_area_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода площади."""
    try:
        area = float(message.text.replace(",", "."))

        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id,
            username=username,
            message=f"Площадь: {area} м²",
            is_bot=False,
        )

        await _process_area(message, state, area, message.from_user.id)

    except (ValueError, AttributeError):
        await message.answer(AREA_INVALID_INPUT, parse_mode=ParseMode.HTML)


async def _process_area(message: Message, state: FSMContext, area: float, user_id: int) -> None:
    """Сохраняет площадь и переходит к выбору профиля."""
    await state.update_data(area=area)

    response = AREA_ACCEPTED.format(area=area)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=response, is_bot=True)

    # Переход к выбору профиля
    await _ask_profile(message, state, user_id)


# ============================================
# ПРОФИЛЬ
# ============================================


async def _ask_profile(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает тип профиля."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.waiting_for_area)
    
    # Отправка фото с вариантами профилей
    # Приоритет: единое фото profiles_all.jpg, иначе первое доступное
    profiles_path = Path("static/images/profiles")
    profile_photo_path = profiles_path / "profiles_all.jpg"
    
    if not profile_photo_path.exists():
        # Fallback: используем первое доступное фото
        for alt_photo in ["insert.jpg", "shadow_eco.jpg", "floating.jpg"]:
            alt_path = profiles_path / alt_photo
            if alt_path.exists():
                profile_photo_path = alt_path
                break
    
    if profile_photo_path.exists():
        try:
            await message.answer_photo(photo=FSInputFile(profile_photo_path))
        except Exception as e:
            logger.error(f"Не удалось отправить изображение профиля {profile_photo_path}: {e}")

    await message.answer(PROFILE_QUESTION, reply_markup=get_profile_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_profile)

    chat_logger.log_message(user_id=user_id, username="БОТ", message=PROFILE_QUESTION, is_bot=True)


@router.callback_query(CalculationStates.choosing_profile, F.data.startswith("profile_"))
async def process_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора профиля."""
    await callback.answer()

    profile_type = callback.data.replace("profile_", "")
    profile_name = get_profile_name(profile_type)

    await state.update_data(profile_type=profile_type)

    username = callback.from_user.username or callback.from_user.first_name
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

    # Если выбран обычный профиль со вставкой, пропускаем карнизы
    if profile_type == "insert":
        await _ask_spotlights(callback.message, state, callback.from_user.id)
    else:
        # Переход к карнизам
        await _ask_cornice_length(callback.message, state, callback.from_user.id)


# ============================================
# КАРНИЗЫ
# ============================================


async def _ask_cornice_length(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает длину карнизов."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.choosing_profile)
    await message.answer(CORNICE_LENGTH_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_cornice_length)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=CORNICE_LENGTH_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_cornice_length)
async def process_cornice_length(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины карнизов."""
    try:
        length = float(message.text.replace(",", "."))

        if length < 0 or length > 100:
            await message.answer(CORNICE_VALIDATION_ERROR, parse_mode=ParseMode.HTML)
            return

        await state.update_data(cornice_length=length)

        if length == 0:
            await message.answer(NO_CORNICE, parse_mode=ParseMode.HTML)
            chat_logger.log_message(
                user_id=message.from_user.id, username="БОТ", message=NO_CORNICE, is_bot=True
            )
            # Переход к освещению
            await _ask_spotlights(message, state, message.from_user.id)
        else:
            # Переход к выбору типа карниза
            await _ask_cornice_type(message, state, message.from_user.id)

    except (ValueError, AttributeError):
        await message.answer(CORNICE_INVALID_INPUT, parse_mode=ParseMode.HTML)


async def _ask_cornice_type(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает тип карниза."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.entering_cornice_length)
    
    # Отправка фото с вариантами карнизов
    # Приоритет: единое фото cornices_all.jpg или carnices_all.jpg, иначе первое доступное
    cornices_path = Path("static/images/cornices")
    cornice_photo_path = cornices_path / "cornices_all.jpg"
    
    # Поддержка опечатки в имени файла
    if not cornice_photo_path.exists():
        cornice_photo_path = cornices_path / "carnices_all.jpg"
    
    if not cornice_photo_path.exists():
        # Fallback: используем первое доступное фото
        for alt_photo in ["pk14.jpg", "pk5.jpg", "bp40.jpg"]:
            alt_path = cornices_path / alt_photo
            if alt_path.exists():
                cornice_photo_path = alt_path
                break
    
    if cornice_photo_path.exists():
        try:
            await message.answer_photo(photo=FSInputFile(cornice_photo_path))
        except Exception as e:
            logger.error(f"Не удалось отправить изображение карниза {cornice_photo_path}: {e}")
 
    await message.answer(CORNICE_TYPE_QUESTION, reply_markup=get_cornice_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_cornice_type)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=CORNICE_TYPE_QUESTION, is_bot=True
    )


@router.callback_query(CalculationStates.choosing_cornice_type, F.data.startswith("cornice_"))
async def process_cornice_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора типа карниза."""
    await callback.answer()

    cornice_type = callback.data.replace("cornice_", "")
    cornice_name = get_cornice_name(cornice_type)

    await state.update_data(cornice_type=cornice_type)

    data = await state.get_data()
    length = data["cornice_length"]

    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Карниз: {cornice_name}, {length} пог.м",
        is_bot=False,
    )

    response = CORNICE_ACCEPTED.format(cornice_name=cornice_name, length=length)
    await callback.message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=response, is_bot=True
    )

    # Переход к освещению
    await _ask_spotlights(callback.message, state, callback.from_user.id)


# ============================================
# ОСВЕЩЕНИЕ - СВЕТИЛЬНИКИ
# ============================================


async def _ask_spotlights(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает количество точечных светильников."""
    # Сохраняем предыдущее состояние (может быть choosing_cornice_type, entering_cornice_length или choosing_profile)
    data = await state.get_data()
    profile_type = data.get("profile_type")
    if profile_type == "insert" or data.get("cornice_length", 0) == 0:
        previous_state = CalculationStates.choosing_profile
    else:
        previous_state = CalculationStates.choosing_cornice_type
    await state.update_data(previous_state=previous_state)
    
    await message.answer(SPOTLIGHTS_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_spotlights)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=SPOTLIGHTS_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_spotlights)
async def process_spotlights_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода светильников."""
    try:
        count = int(message.text)

        if count < 0 or count > 100:
            await message.answer(COUNT_VALIDATION_ERROR, parse_mode=ParseMode.HTML)
            return

        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id,
            username=username,
            message=f"Светильники: {count} шт",
            is_bot=False,
        )

        await _process_spotlights(message, state, count, message.from_user.id)

    except (ValueError, AttributeError):
        await message.answer(SPOTLIGHTS_INVALID_INPUT, parse_mode=ParseMode.HTML)


async def _process_spotlights(
    message: Message, state: FSMContext, count: int, user_id: int
) -> None:
    """Сохраняет количество светильников и переходит к люстрам."""
    await state.update_data(spotlights=count)

    response = SPOTLIGHTS_ACCEPTED.format(count=count)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user_id, username="БОТ", message=response, is_bot=True)

    # Переход к люстрам
    await _ask_chandeliers(message, state, user_id)


# ============================================
# ОСВЕЩЕНИЕ - ЛЮСТРЫ
# ============================================


async def _ask_chandeliers(message: Message, state: FSMContext, user_id: int) -> None:
    """Запрашивает количество люстр."""
    # Сохраняем предыдущее состояние
    await state.update_data(previous_state=CalculationStates.entering_spotlights)
    await message.answer(CHANDELIERS_QUESTION, reply_markup=get_back_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.entering_chandeliers)

    chat_logger.log_message(
        user_id=user_id, username="БОТ", message=CHANDELIERS_QUESTION, is_bot=True
    )


@router.message(CalculationStates.entering_chandeliers)
async def process_chandeliers_input(message: Message, state: FSMContext) -> None:
    """Обработка текстового ввода люстр."""
    try:
        count = int(message.text)

        if count < 0 or count > 100:
            await message.answer(COUNT_VALIDATION_ERROR, parse_mode=ParseMode.HTML)
            return

        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id,
            username=username,
            message=f"Люстры: {count} шт",
            is_bot=False,
        )

        await _process_chandeliers(message, state, count, message.from_user)

    except (ValueError, AttributeError):
        await message.answer(CHANDELIERS_INVALID_INPUT, parse_mode=ParseMode.HTML)


async def _process_chandeliers(
    message: Message, state: FSMContext, count: int, user: User
) -> None:
    """Сохраняет количество люстр и показывает результат."""
    await state.update_data(chandeliers=count)

    response = CHANDELIERS_ACCEPTED.format(count=count)
    await message.answer(response, parse_mode=ParseMode.HTML)
    chat_logger.log_message(user_id=user.id, username="БОТ", message=response, is_bot=True)

    # Переход к результату
    await _show_result(message, state, user)


# ============================================
# РЕЗУЛЬТАТ И ОТПРАВКА АДМИНУ
# ============================================


def _format_result_info(calculation: CalculationData) -> tuple[str, str, str]:
    """Формирует информацию о расчёте для отображения.
    
    Args:
        calculation: Данные расчёта
        
    Returns:
        (area_note, cornice_info, lighting_info)
    """
    area_note = ""
    if calculation.area < settings.min_area_for_calculation:
        area_note = f"• Расчёт от минимальной площади: {calculation.area_for_calculation} м²\n"

    cornice_info = ""
    if calculation.cornice_length > 0 and calculation.cornice_type:
        cornice_name = get_cornice_name(calculation.cornice_type)
        cornice_info = f"• Карниз: {cornice_name} — {calculation.cornice_length} пог.м\n"

    lighting_info = ""
    if calculation.spotlights > 0:
        lighting_info += f"• Точечные светильники: {calculation.spotlights} шт\n"
    if calculation.chandeliers > 0:
        lighting_info += f"• Люстры: {calculation.chandeliers} шт\n"

    return area_note, cornice_info, lighting_info


async def _show_result(message: Message, state: FSMContext, user: User) -> None:
    """Показывает результат расчёта и отправляет админу."""
    # Получение данных
    data = await state.get_data()

    # Расчёт
    calculation = calculate_total(data)

    # Формирование сообщения для пользователя
    area_note, cornice_info, lighting_info = _format_result_info(calculation)
    profile_name = get_profile_name(calculation.profile_type)

    result_text = RESULT_MESSAGE.format(
        area=calculation.area,
        area_note=area_note,
        profile_name=profile_name,
        cornice_info=cornice_info,
        lighting_info=lighting_info,
        total=calculation.total_cost,
    )

    await message.answer(result_text, reply_markup=get_result_keyboard(), parse_mode=ParseMode.HTML)

    await state.set_state(CalculationStates.showing_result)

    chat_logger.log_message(user_id=user.id, username="БОТ", message=result_text, is_bot=True)

    # Отправка уведомления админу
    await _notify_admin(message.bot, user, calculation, data)


async def _notify_admin(bot: Bot, user: User, calculation, data: dict) -> None:
    """Отправляет уведомление админам о завершении расчёта."""
    if not bot or not settings.admin_ids_list:
        return

    try:
        username = f"@{user.username}" if user.username else "нет username"
        date = datetime.now().strftime("%d.%m.%Y %H:%M")

        profile_name = get_profile_name(calculation.profile_type)
        area_note, cornice_info, lighting_info = _format_result_info(calculation)

        # Детализация
        details = RESULT_DETAILS_CEILING.format(
            area_calc=calculation.area_for_calculation, cost=calculation.ceiling_cost
        )

        if calculation.profile_cost > 0:
            details += RESULT_DETAILS_PROFILE.format(
                name=profile_name, cost=calculation.profile_cost
            )

        if calculation.cornice_cost > 0:
            cornice_name = get_cornice_name(calculation.cornice_type)
            details += RESULT_DETAILS_CORNICE.format(
                type=cornice_name, length=calculation.cornice_length, cost=calculation.cornice_cost
            )

        if calculation.spotlights_cost > 0:
            details += RESULT_DETAILS_SPOTLIGHTS.format(
                count=calculation.spotlights, cost=calculation.spotlights_cost
            )

        if calculation.chandeliers_cost > 0:
            details += RESULT_DETAILS_CHANDELIERS.format(
                count=calculation.chandeliers, cost=calculation.chandeliers_cost
            )

        admin_report = ADMIN_REPORT.format(
            user_id=user.id,
            username=username,
            full_name=user.full_name,
            date=date,
            area=calculation.area,
            area_note=area_note,
            profile_name=profile_name,
            cornice_info=cornice_info,
            lighting_info=lighting_info,
            total=calculation.total_cost,
            details=details,
        )

        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_report)
            except Exception as e:
                error_msg = str(e).lower()
                if "chat not found" not in error_msg and "bot was blocked" not in error_msg:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админу: {e}")
