"""Обработчик команды /start."""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards.inline import get_start_keyboard
from app.templates.messages.texts import START_MESSAGE
from app.services.chat_logger import chat_logger

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start."""
    await state.clear()
    
    username = message.from_user.username or message.from_user.first_name
    chat_logger.log_message(
        user_id=message.from_user.id,
        username=username,
        message="/start",
        is_bot=False
    )
    
    await message.answer(
        START_MESSAGE,
        reply_markup=get_start_keyboard()
    )
    
    chat_logger.log_message(
        user_id=message.from_user.id,
        username="БОТ",
        message=START_MESSAGE,
        is_bot=True
    )


@router.callback_query(F.data == "start_calculation")
async def start_calculation(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса расчёта."""
    await callback.answer()
    await state.clear()
    
    from app.bot.handlers.calculation import ask_area
    if callback.message:
        await ask_area(callback.message, state)

