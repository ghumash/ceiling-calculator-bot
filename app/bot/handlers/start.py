"""Обработчик команды /start."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards.inline import get_contact_method_keyboard
from app.bot.states import CalculationStates
from app.templates.messages.texts import WELCOME_MESSAGE, MANAGER_CONTACTS
from app.services.chat_logger import chat_logger
from app.core.config import settings
from app.bot.handlers.calculation import ask_area

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    await state.clear()

    username = message.from_user.username or message.from_user.first_name
    chat_logger.log_message(
        user_id=message.from_user.id, username=username, message="/start", is_bot=False
    )

    await message.answer(WELCOME_MESSAGE, reply_markup=get_contact_method_keyboard())
    await state.set_state(CalculationStates.choosing_contact_method)

    chat_logger.log_message(
        user_id=message.from_user.id, username="БОТ", message=WELCOME_MESSAGE, is_bot=True
    )


@router.callback_query(F.data == "start_calculation")
async def start_new_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало нового расчёта — показ приветствия и выбора способа связи."""
    await callback.answer()
    await state.clear()

    # Очистка истории чата для нового расчёта
    if callback.from_user:
        chat_logger.clear_chat_history(callback.from_user.id)

    await callback.message.answer(
        text=WELCOME_MESSAGE,
        reply_markup=get_contact_method_keyboard()
    )

    await state.set_state(CalculationStates.choosing_contact_method)

    chat_logger.log_message(
        user_id=callback.from_user.id,
        username="БОТ",
        message=WELCOME_MESSAGE,
        is_bot=True
    )


@router.callback_query(F.data == "method_manager")
async def contact_manager(callback: CallbackQuery, state: FSMContext) -> None:
    """Связь с менеджером."""
    await callback.answer()

    contacts = MANAGER_CONTACTS.format(
        phone=settings.contact_phone,
        telegram=settings.contact_telegram
    )

    await callback.message.answer(text=contacts)
    
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
    await callback.answer()
    await ask_area(callback.message, state, callback.from_user.id)
