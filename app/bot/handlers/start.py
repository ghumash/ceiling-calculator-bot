"""Обработчик команды /start."""

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards.inline import get_contact_method_keyboard, get_edit_params_keyboard
from app.bot.states import CalculationStates
from app.templates.messages.texts import (
    WELCOME_MESSAGE,
    MANAGER_CONTACTS,
    EDIT_PARAMS_MESSAGE,
    NO_CALCULATION_MESSAGE,
)
from app.services.chat_logger import chat_logger
from app.core.config import settings
from app.bot.handlers.calculation import ask_area
from app.utils.user import get_user_display_name
from app.utils.callback import safe_answer_callback

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    await state.clear()

    username = get_user_display_name(message.from_user)
    user_name = message.from_user.first_name or "Пользователь"
    chat_logger.log_message(
        user_id=message.from_user.id, username=username, message="/start", is_bot=False
    )

    welcome_text = WELCOME_MESSAGE.format(name=user_name)
    await message.answer(welcome_text, reply_markup=get_contact_method_keyboard(), parse_mode=ParseMode.HTML)
    await state.set_state(CalculationStates.choosing_contact_method)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=welcome_text, is_bot=True
    )


@router.callback_query(F.data == "start_calculation")
async def start_new_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало нового расчёта — показ приветствия и выбора способа связи."""
    await safe_answer_callback(callback)
    await state.clear()

    # Очистка истории чата для нового расчёта
    if callback.from_user:
        chat_logger.clear_chat_history(callback.from_user.id)

    user_name = callback.from_user.first_name or "Пользователь"
    welcome_text = WELCOME_MESSAGE.format(name=user_name)

    await callback.message.answer(
        text=welcome_text,
        reply_markup=get_contact_method_keyboard(),
        parse_mode=ParseMode.HTML
    )

    await state.set_state(CalculationStates.choosing_contact_method)

    chat_logger.log_message(
        user_id=callback.from_user.id,
        username="БОТ",
        message=welcome_text,
        is_bot=True
    )


@router.callback_query(F.data == "method_manager")
async def contact_manager(callback: CallbackQuery, state: FSMContext) -> None:
    """Связь с менеджером."""
    await safe_answer_callback(callback)

    contacts = MANAGER_CONTACTS.format(
        phone=settings.contact_phone,
        telegram=settings.contact_telegram
    )

    await callback.message.answer(text=contacts, parse_mode=ParseMode.HTML)
    
    # Очищаем состояние только если мы в процессе выбора способа связи
    current_state = await state.get_state()
    if current_state == CalculationStates.choosing_contact_method:
        await state.clear()

    chat_logger.log_message(
        user_id=callback.from_user.id,
        username="БОТ",
        message=contacts,
        is_bot=True
    )


@router.callback_query(CalculationStates.choosing_contact_method, F.data == "method_bot")
async def start_bot_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало автоматического расчёта — переход к вопросу о площади."""
    await safe_answer_callback(callback)
    await ask_area(callback.message, state, callback.from_user.id)


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext) -> None:
    """Обработчик команды /edit — редактирование параметров."""
    data = await state.get_data()
    
    username = get_user_display_name(message.from_user)
    chat_logger.log_message(
        user_id=message.from_user.id, username=username, message="/edit", is_bot=False
    )
    
    # Проверяем наличие активного расчёта
    if not data.get("area"):
        await message.answer(NO_CALCULATION_MESSAGE, parse_mode=ParseMode.HTML)
        chat_logger.log_message(
            user_id=message.from_user.id, username="БОТ", message=NO_CALCULATION_MESSAGE, is_bot=True
        )
        return
    
    await message.answer(
        EDIT_PARAMS_MESSAGE,
        reply_markup=get_edit_params_keyboard(data),
        parse_mode=ParseMode.HTML
    )
    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=EDIT_PARAMS_MESSAGE, is_bot=True
    )
