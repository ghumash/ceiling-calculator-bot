"""Обработчик FSM диалога расчёта."""

import logging
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, User

from app.bot.states import CalculationStates
from app.bot.keyboards.inline import (
    get_quick_area_keyboard,
    get_corners_keyboard,
    get_quick_perimeter_keyboard,
    get_fabric_keyboard,
    get_profile_keyboard,
    get_yes_no_keyboard,
    get_cornice_keyboard,
    get_spotlights_keyboard,
    get_chandeliers_keyboard,
    get_calculate_keyboard,
    get_result_keyboard,
)
from app.templates.messages.texts import (
    AREA_QUESTION,
    AREA_VALIDATION_ERROR,
    AREA_INVALID_INPUT,
    CORNERS_QUESTION,
    PERIMETER_QUESTION,
    PERIMETER_VALIDATION_ERROR,
    PERIMETER_INVALID_INPUT,
    FABRIC_QUESTION,
    PROFILE_QUESTION,
    CORNICES_QUESTION,
    CORNICE_LENGTH_QUESTION,
    SPOTLIGHTS_QUESTION,
    SPOTLIGHTS_INVALID_INPUT,
    CERAMIC_QUESTION,
    CERAMIC_AREA_QUESTION,
    CERAMIC_AREA_INVALID_INPUT,
    CHANDELIERS_QUESTION,
    CHANDELIERS_INVALID_INPUT,
    ALL_QUESTIONS_COMPLETE,
    GENERATING_RESULT,
    format_result_message,
)
from app.services.chat_logger import chat_logger
from app.services.calculator import calculate_total_cost
from app.schemas.calculation import CalculationData

logger = logging.getLogger(__name__)
router = Router()


# ========== ПЛОЩАДЬ ==========


async def ask_area(message: Message, state: FSMContext) -> None:
    """Запрашивает площадь помещения."""
    await message.answer(AREA_QUESTION, reply_markup=get_quick_area_keyboard())
    await state.set_state(CalculationStates.waiting_for_area)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=AREA_QUESTION, is_bot=True
    )


@router.callback_query(F.data.startswith("area_"))
async def process_area_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка быстрых кнопок площади."""
    await callback.answer()

    if callback.data == "area_custom":
        custom_message = "Введите площадь в м²:"
        await callback.message.answer(custom_message)
        await state.set_state(CalculationStates.waiting_for_area)
        # Логирование вопроса бота
        chat_logger.log_message(
            user_id=callback.from_user.id, username="БОТ", message=custom_message, is_bot=True
        )
        return

    area_value = float(callback.data.split("_")[1])
    # Логирование выбора площади через callback
    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Площадь: {area_value} м²",
        is_bot=False,
    )
    # Временно сохраняем флаг, что логирование уже сделано
    await state.update_data(_area_logged=True)
    await process_area(callback.message, state, area_value)


@router.message(CalculationStates.waiting_for_area)
async def process_area_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода площади."""
    try:
        area = float(message.text.replace(",", "."))

        if not (5 <= area <= 200):
            await message.answer(AREA_VALIDATION_ERROR)
            return

        await process_area(message, state, area)

    except (ValueError, AttributeError):
        await message.answer(AREA_INVALID_INPUT)


async def process_area(message: Message, state: FSMContext, area: float) -> None:
    """Сохраняет площадь и переходит к следующему шагу."""
    await state.update_data(area=area)

    # Логирование для текстового ввода (если не было callback)
    data = await state.get_data()
    if not data.get("_area_logged"):
        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id,
            username=username,
            message=f"Площадь: {area} м²",
            is_bot=False,
        )
    await state.update_data(_area_logged=False)  # Сбрасываем флаг

    await message.answer(CORNERS_QUESTION, reply_markup=get_corners_keyboard())
    await state.set_state(CalculationStates.waiting_for_corners)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=CORNERS_QUESTION, is_bot=True
    )


# ========== УГЛЫ ==========


@router.callback_query(F.data.startswith("corners_"), CalculationStates.waiting_for_corners)
async def process_corners(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора количества углов."""
    await callback.answer()

    corners_str = callback.data.split("_")[1]
    corners = 8 if corners_str == "8" else int(corners_str)

    await state.update_data(corners=corners)

    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id, username=username, message=f"Углов: {corners}", is_bot=False
    )

    await callback.message.answer(PERIMETER_QUESTION, reply_markup=get_quick_perimeter_keyboard())
    await state.set_state(CalculationStates.waiting_for_perimeter)

    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=PERIMETER_QUESTION, is_bot=True
    )


# ========== ПЕРИМЕТР ==========


@router.callback_query(F.data.startswith("perimeter_"))
async def process_perimeter_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка быстрых кнопок периметра."""
    await callback.answer()

    if callback.data == "perimeter_custom":
        custom_message = "Введите периметр в пог.м:"
        await callback.message.answer(custom_message)
        await state.set_state(CalculationStates.waiting_for_perimeter)
        # Логирование вопроса бота
        chat_logger.log_message(
            user_id=callback.from_user.id, username="БОТ", message=custom_message, is_bot=True
        )
        return

    perimeter_value = float(callback.data.split("_")[1])
    # Логирование выбора периметра
    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Периметр: {perimeter_value} пог.м",
        is_bot=False,
    )
    await process_perimeter(callback.message, state, perimeter_value)


@router.message(CalculationStates.waiting_for_perimeter)
async def process_perimeter_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода периметра."""
    try:
        perimeter = float(message.text.replace(",", "."))

        if perimeter <= 0:
            await message.answer(PERIMETER_VALIDATION_ERROR)
            return

        await process_perimeter(message, state, perimeter)

    except (ValueError, AttributeError):
        await message.answer(PERIMETER_INVALID_INPUT)


async def process_perimeter(message: Message, state: FSMContext, perimeter: float) -> None:
    """Сохраняет периметр и переходит к выбору полотна."""
    await state.update_data(perimeter=perimeter)

    # Логирование для текстового ввода (если не было callback)
    username = message.from_user.username or message.from_user.first_name
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Периметр: {perimeter} пог.м",
        is_bot=False,
    )

    # Отправка изображений полотен
    await send_fabric_images(message)

    await message.answer(FABRIC_QUESTION, reply_markup=get_fabric_keyboard())
    await state.set_state(CalculationStates.choosing_fabric)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=FABRIC_QUESTION, is_bot=True
    )


async def send_fabric_images(message: Message) -> None:
    """Отправляет изображения полотен."""
    msd_path = Path("static/images/fabrics/msd.jpg")
    bauf_path = Path("static/images/fabrics/bauf.jpg")

    if msd_path.exists():
        try:
            photo = FSInputFile(msd_path)
            await message.answer_photo(photo, caption="🇨🇳 MSD — стандартное качество")
        except Exception as e:
            logger.warning(f"Не удалось отправить изображение MSD: {e}")

    if bauf_path.exists():
        try:
            photo = FSInputFile(bauf_path)
            await message.answer_photo(photo, caption="🇩🇪 BAUF — премиум качество")
        except Exception as e:
            logger.warning(f"Не удалось отправить изображение BAUF: {e}")


# ========== ПОЛОТНО ==========


@router.callback_query(F.data.startswith("fabric_"), CalculationStates.choosing_fabric)
async def process_fabric(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора полотна."""
    await callback.answer()

    fabric_type = callback.data.split("_")[1]  # msd или bauf

    await state.update_data(fabric_type=fabric_type)

    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Полотно: {fabric_type}",
        is_bot=False,
    )

    # Отправка изображений профилей
    await send_profile_images(callback.message)

    await callback.message.answer(PROFILE_QUESTION, reply_markup=get_profile_keyboard())
    await state.set_state(CalculationStates.choosing_profile)

    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=PROFILE_QUESTION, is_bot=True
    )


async def send_profile_images(message: Message) -> None:
    """Отправляет изображения профилей."""
    profile_images = {
        "insert": "static/images/profiles/insert.jpg",
        "shadow_eco": "static/images/profiles/shadow_eco.jpg",
        "shadow_eurokraab": "static/images/profiles/shadow_eurokraab.jpg",
        "floating": "static/images/profiles/floating.jpg",
        "am1": "static/images/profiles/am1.jpg",
    }

    for profile_type, image_path in profile_images.items():
        path = Path(image_path)
        if path.exists():
            try:
                photo = FSInputFile(path)
                captions = {
                    "insert": "📎 Со вставкой",
                    "shadow_eco": "🌑 Теневой ЭКОНОМ",
                    "shadow_eurokraab": "🌑 Теневой EuroKraab",
                    "floating": "☁️ Парящий",
                    "am1": "✨ Однородный AM1",
                }
                await message.answer_photo(photo, caption=captions.get(profile_type, ""))
            except Exception as e:
                logger.warning(f"Не удалось отправить изображение профиля {profile_type}: {e}")


# ========== ПРОФИЛЬ ==========


@router.callback_query(F.data.startswith("profile_"), CalculationStates.choosing_profile)
async def process_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора профиля."""
    await callback.answer()

    profile_type = callback.data.replace("profile_", "")

    await state.update_data(profile_type=profile_type)

    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Профиль: {profile_type}",
        is_bot=False,
    )

    await callback.message.answer(CORNICES_QUESTION, reply_markup=get_yes_no_keyboard())
    await state.set_state(CalculationStates.asking_cornices)

    chat_logger.log_message(
        user_id=callback.from_user.id, username="БОТ", message=CORNICES_QUESTION, is_bot=True
    )


# ========== КАРНИЗЫ ==========


@router.callback_query(F.data.in_(["yes", "no"]), CalculationStates.asking_cornices)
async def process_cornices_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора карнизов."""
    await callback.answer()

    has_cornices = callback.data == "yes"
    await state.update_data(has_cornices=has_cornices)

    if has_cornices:
        # Отправка изображений карнизов
        await send_cornice_images(callback.message)

        await callback.message.answer("Выберите тип карниза:", reply_markup=get_cornice_keyboard())
        await state.set_state(CalculationStates.choosing_cornice)

        chat_logger.log_message(
            user_id=callback.from_user.id,
            username="БОТ",
            message="Выберите тип карниза:",
            is_bot=True,
        )
    else:
        await state.update_data(cornice_type=None, cornice_length=None)
        await ask_spotlights(callback.message, state)


async def send_cornice_images(message: Message) -> None:
    """Отправляет изображения карнизов."""
    cornice_images = {
        "pk14": "static/images/cornices/pk14.jpg",
        "pk5": "static/images/cornices/pk5.jpg",
        "bp40": "static/images/cornices/bp40.jpg",
    }

    for cornice_type, image_path in cornice_images.items():
        path = Path(image_path)
        if path.exists():
            try:
                photo = FSInputFile(path)
                await message.answer_photo(photo, caption=f"Карниз {cornice_type.upper()}")
            except Exception as e:
                logger.warning(f"Не удалось отправить изображение карниза {cornice_type}: {e}")


@router.callback_query(F.data.startswith("cornice_"), CalculationStates.choosing_cornice)
async def process_cornice(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора карниза."""
    await callback.answer()

    cornice_type = callback.data.replace("cornice_", "")
    await state.update_data(cornice_type=cornice_type)

    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Карниз: {cornice_type}",
        is_bot=False,
    )

    # Если нужна длина (pk5 или bp40)
    if cornice_type in ["pk5", "bp40"]:
        await callback.message.answer(CORNICE_LENGTH_QUESTION)
        await state.set_state(CalculationStates.entering_cornice_length)

        chat_logger.log_message(
            user_id=callback.from_user.id,
            username="БОТ",
            message=CORNICE_LENGTH_QUESTION,
            is_bot=True,
        )
    else:
        await state.update_data(cornice_length=None)
        await ask_spotlights(callback.message, state)


@router.message(CalculationStates.entering_cornice_length)
async def process_cornice_length(message: Message, state: FSMContext) -> None:
    """Обработка ввода длины карниза."""
    try:
        length = float(message.text.replace(",", "."))

        if length <= 0:
            await message.answer("⚠️ Длина должна быть больше 0")
            return

        await state.update_data(cornice_length=length)

        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id, username=username, message=str(length), is_bot=False
        )

        await ask_spotlights(message, state)

    except (ValueError, AttributeError):
        await message.answer("⚠️ Пожалуйста, укажите число.\nНапример: 3.5")


# ========== ОСВЕЩЕНИЕ ==========


async def ask_spotlights(message: Message, state: FSMContext) -> None:
    """Запрашивает количество светильников."""
    await message.answer(SPOTLIGHTS_QUESTION, reply_markup=get_spotlights_keyboard())
    await state.set_state(CalculationStates.entering_spotlights)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=SPOTLIGHTS_QUESTION, is_bot=True
    )


@router.callback_query(F.data.startswith("spotlights_"))
async def process_spotlights_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка быстрых кнопок светильников."""
    await callback.answer()

    if callback.data == "spotlights_custom":
        custom_message = "Введите количество светильников:"
        await callback.message.answer(custom_message)
        await state.set_state(CalculationStates.entering_spotlights)
        # Логирование вопроса бота
        chat_logger.log_message(
            user_id=callback.from_user.id, username="БОТ", message=custom_message, is_bot=True
        )
        return

    spotlights_value = int(callback.data.split("_")[1])
    # Логирование выбора светильников
    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Светильники: {spotlights_value} шт",
        is_bot=False,
    )
    await process_spotlights(callback.message, state, spotlights_value)


@router.message(CalculationStates.entering_spotlights)
async def process_spotlights_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода количества светильников."""
    try:
        spotlights = int(message.text)

        if spotlights < 0:
            await message.answer("⚠️ Количество не может быть отрицательным")
            return

        await process_spotlights(message, state, spotlights)

    except (ValueError, AttributeError):
        await message.answer(SPOTLIGHTS_INVALID_INPUT)


async def process_spotlights(message: Message, state: FSMContext, spotlights: int) -> None:
    """Сохраняет количество светильников и переходит к керамограниту."""
    await state.update_data(spotlights=spotlights)

    # Логирование для текстового ввода (если не было callback)
    username = message.from_user.username or message.from_user.first_name
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Светильники: {spotlights} шт",
        is_bot=False,
    )

    await message.answer(CERAMIC_QUESTION, reply_markup=get_yes_no_keyboard())
    await state.set_state(CalculationStates.asking_ceramic)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=CERAMIC_QUESTION, is_bot=True
    )


@router.callback_query(F.data.in_(["yes", "no"]), CalculationStates.asking_ceramic)
async def process_ceramic_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора керамогранита."""
    await callback.answer()

    has_ceramic = callback.data == "yes"
    await state.update_data(has_ceramic=has_ceramic)

    if has_ceramic:
        await callback.message.answer(CERAMIC_AREA_QUESTION)
        await state.set_state(CalculationStates.entering_ceramic_area)

        chat_logger.log_message(
            user_id=callback.from_user.id,
            username="БОТ",
            message=CERAMIC_AREA_QUESTION,
            is_bot=True,
        )
    else:
        await state.update_data(ceramic_area=0.0)
        await ask_chandeliers(callback.message, state)


@router.message(CalculationStates.entering_ceramic_area)
async def process_ceramic_area(message: Message, state: FSMContext) -> None:
    """Обработка ввода площади керамогранита."""
    try:
        ceramic_area = float(message.text.replace(",", "."))

        if ceramic_area < 0:
            await message.answer("⚠️ Площадь не может быть отрицательной")
            return

        await state.update_data(ceramic_area=ceramic_area)

        username = message.from_user.username or message.from_user.first_name
        chat_logger.log_message(
            user_id=message.from_user.id,
            username=username,
            message=f"Керамогранит: {ceramic_area} пог.м",
            is_bot=False,
        )

        await ask_chandeliers(message, state)

    except (ValueError, AttributeError):
        await message.answer(CERAMIC_AREA_INVALID_INPUT)


async def ask_chandeliers(message: Message, state: FSMContext) -> None:
    """Запрашивает количество люстр."""
    await message.answer(CHANDELIERS_QUESTION, reply_markup=get_chandeliers_keyboard())
    await state.set_state(CalculationStates.entering_chandeliers)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=CHANDELIERS_QUESTION, is_bot=True
    )


@router.callback_query(F.data.startswith("chandeliers_"))
async def process_chandeliers_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка быстрых кнопок люстр."""
    await callback.answer()

    chandeliers_value = int(callback.data.split("_")[1])
    # Логирование выбора люстр
    username = callback.from_user.username or callback.from_user.first_name
    chat_logger.log_message(
        user_id=callback.from_user.id,
        username=username,
        message=f"Люстры: {chandeliers_value} шт",
        is_bot=False,
    )
    await process_chandeliers(callback.message, state, chandeliers_value)


@router.message(CalculationStates.entering_chandeliers)
async def process_chandeliers_input(message: Message, state: FSMContext) -> None:
    """Обработка ввода количества люстр."""
    try:
        chandeliers = int(message.text)

        if chandeliers < 0:
            await message.answer("⚠️ Количество не может быть отрицательным")
            return

        await process_chandeliers(message, state, chandeliers)

    except (ValueError, AttributeError):
        await message.answer(CHANDELIERS_INVALID_INPUT)


async def process_chandeliers(message: Message, state: FSMContext, chandeliers: int) -> None:
    """Сохраняет количество люстр и показывает кнопку 'Рассчитать'."""
    await state.update_data(chandeliers=chandeliers)

    # Логирование для текстового ввода (если не было callback)
    username = message.from_user.username or message.from_user.first_name
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message=f"Люстры: {chandeliers} шт",
        is_bot=False,
    )

    # Показываем кнопку "Рассчитать" вместо автоматического расчёта
    await message.answer(ALL_QUESTIONS_COMPLETE, reply_markup=get_calculate_keyboard())
    await state.set_state(CalculationStates.ready_to_calculate)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=ALL_QUESTIONS_COMPLETE, is_bot=True
    )


# ========== РАСЧЁТ ==========


@router.callback_query(F.data == "calculate", CalculationStates.ready_to_calculate)
async def calculate_result(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка нажатия кнопки 'Рассчитать'."""
    await callback.answer()

    if callback.message:
        await show_result(callback.message, state, user=callback.from_user)


# ========== РЕЗУЛЬТАТ ==========


async def show_result(message: Message, state: FSMContext, user: User | None = None) -> None:
    """Показывает результат расчёта.

    Args:
        message: Сообщение для ответа
        state: FSM контекст
        user: Пользователь (если None, используется message.from_user)
    """
    # Определяем пользователя: если передан явно (из callback), используем его, иначе message.from_user
    actual_user = user if user is not None else message.from_user
    user_id = actual_user.id

    data = await state.get_data()

    # Создание CalculationData
    calc_data = CalculationData(
        area=data["area"],
        corners=data["corners"],
        perimeter=data["perimeter"],
        fabric_type=data["fabric_type"],
        profile_type=data["profile_type"],
        has_cornices=data.get("has_cornices", False),
        cornice_type=data.get("cornice_type"),
        cornice_length=data.get("cornice_length"),
        spotlights=data.get("spotlights", 0),
        has_ceramic=data.get("has_ceramic", False),
        ceramic_area=data.get("ceramic_area", 0.0),
        chandeliers=data.get("chandeliers", 0),
    )

    # Расчёт стоимости
    costs = calculate_total_cost(calc_data)

    # Формирование сообщения
    result_data = {
        "area": calc_data.area,
        "perimeter": calc_data.perimeter,
        "corners": calc_data.corners,
        "fabric_type": calc_data.fabric_type,
        "profile_type": calc_data.profile_type,
        "spotlights": calc_data.spotlights,
        "ceramic_area": calc_data.ceramic_area,
        "chandeliers": calc_data.chandeliers,
        **costs,
    }

    await message.answer(GENERATING_RESULT)

    result_text = format_result_message(result_data)
    await message.answer(result_text, reply_markup=get_result_keyboard())

    await state.update_data(calculation_data=calc_data.model_dump())
    await state.set_state(CalculationStates.showing_result)

    chat_logger.log_message(user_id=user_id, username="БОТ", message=result_text, is_bot=True)

    # Отправка уведомления админу с полным чатом
    chat_history = chat_logger.get_chat_history(user_id)
    total_cost = costs.get("total_cost", 0.0)
    await notify_admin_calculation_complete(
        user=actual_user,
        bot=message.bot,
        calc_data=calc_data,
        total_cost=total_cost,
        chat_history=chat_history,
    )


def _format_username(user: User) -> str:
    """Форматирует имя пользователя для уведомления.

    Args:
        user: Объект пользователя Telegram

    Returns:
        Отформатированное имя пользователя
    """
    if user.username:
        return f"@{user.username}"
    name_parts = [user.first_name or "", user.last_name or ""]
    return " ".join(filter(None, name_parts)) or f"user_{user.id}"


def _format_cornice_info(calc_data: CalculationData) -> str:
    """Форматирует информацию о карнизе.

    Args:
        calc_data: Данные расчёта

    Returns:
        Строка с информацией о карнизе
    """
    if not calc_data.has_cornices or not calc_data.cornice_type:
        return "• Карниз: Нет\n"

    cornice_names = {
        "pk14_2m": "ПК-14 (2 м)",
        "pk14_3_2m": "ПК-14 (3.2 м)",
        "pk14_3_6m": "ПК-14 (3.6 м)",
        "pk5": f"ПК-5 ({calc_data.cornice_length or 0} пог.м)"
        if calc_data.cornice_length
        else "ПК-5",
        "bp40": f"БП-40 ({calc_data.cornice_length or 0} пог.м)"
        if calc_data.cornice_length
        else "БП-40",
    }
    cornice_name = cornice_names.get(calc_data.cornice_type, calc_data.cornice_type)
    return f"• Карниз: {cornice_name}\n"


def _format_admin_notification_header(
    username: str, user_id: int, date: str, total_cost: float, calc_data: CalculationData
) -> str:
    """Форматирует заголовок уведомления админу.

    Args:
        username: Имя пользователя
        user_id: ID пользователя
        date: Дата в формате строки
        total_cost: Итоговая стоимость
        calc_data: Данные расчёта

    Returns:
        Отформатированный заголовок
    """
    fabric_names = {"msd": "MSD", "bauf": "BAUF"}
    profile_names = {
        "insert": "Со вставкой",
        "shadow_eco": "Теневой Эконом",
        "shadow_eurokraab": "Теневой EuroKraab",
        "floating": "Парящий",
        "am1": "Однородный AM1",
    }

    cornice_info = _format_cornice_info(calc_data)

    return (
        "✅ РАСЧЁТ ЗАВЕРШЁН\n\n"
        f"Пользователь: {username} (ID: {user_id})\n"
        f"Дата: {date}\n"
        f"Сумма: {total_cost:,.0f} ₽\n\n"
        f"Параметры:\n"
        f"• Площадь: {calc_data.area} м²\n"
        f"• Периметр: {calc_data.perimeter} пог.м\n"
        f"• Углов: {calc_data.corners}\n"
        f"• Полотно: {fabric_names.get(calc_data.fabric_type, calc_data.fabric_type)}\n"
        f"• Профиль: {profile_names.get(calc_data.profile_type, calc_data.profile_type)}\n"
        f"{cornice_info}"
        f"• Светильники: {calc_data.spotlights} шт\n"
        f"• Люстры: {calc_data.chandeliers} шт\n"
        f"• Керамогранит: {calc_data.ceramic_area} пог.м\n\n"
        f"{'=' * 50}\n"
        f"📝 ПОЛНАЯ ИСТОРИЯ ЧАТА:\n"
        f"{'=' * 50}\n\n"
    )


def _truncate_message_if_needed(header: str, chat_history: str) -> str:
    """Обрезает сообщение, если оно превышает лимит Telegram.

    Args:
        header: Заголовок сообщения
        chat_history: История чата

    Returns:
        Полное сообщение (обрезанное при необходимости)
    """
    max_length = 4096
    full_message = header + chat_history

    if len(full_message) > max_length:
        available_length = max_length - len(header) - 50
        truncated_history = chat_history[-available_length:]
        return header + "...\n" + truncated_history

    return full_message


async def notify_admin_calculation_complete(
    user: User, bot: Bot, calc_data: CalculationData, total_cost: float, chat_history: str
) -> None:
    """Отправляет уведомление админам о завершении расчёта с полным чатом.

    Args:
        user: Объект пользователя Telegram
        bot: Объект бота
        calc_data: Данные расчёта
        total_cost: Итоговая стоимость
        chat_history: Полная история чата
    """
    from datetime import datetime
    from app.core.config import settings

    if not bot or not settings.admin_ids_list:
        return

    try:
        username = _format_username(user)
        user_id = user.id
        date = datetime.now().strftime("%d.%m.%Y %H:%M")

        header = _format_admin_notification_header(username, user_id, date, total_cost, calc_data)
        full_message = _truncate_message_if_needed(header, chat_history)

        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(admin_id, full_message)
            except Exception as e:
                error_msg = str(e).lower()
                if "chat not found" not in error_msg and "bot was blocked" not in error_msg:
                    logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админу: {e}")


@router.callback_query(F.data == "contact_manager")
async def contact_manager(callback: CallbackQuery) -> None:
    """Обработка запроса связи с менеджером."""
    await callback.answer()

    from app.core.config import settings

    await callback.message.answer(
        f"📞 Свяжитесь с нами:\n\n"
        f"Телефон: {settings.contact_phone}\n"
        f"Telegram: {settings.contact_telegram}"
    )
