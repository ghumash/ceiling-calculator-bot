"""Утилиты для работы с callback queries."""

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    """Безопасно отвечает на callback query, игнорируя ошибки устаревших запросов.
    
    Args:
        callback: Callback query для ответа
        text: Опциональный текст для отображения пользователю
    """
    try:
        await callback.answer(text=text)
    except TelegramBadRequest as e:
        # Игнорируем ошибки устаревших callback queries
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            logger.debug(f"Игнорируем устаревший callback query: {e}")
        else:
            # Логируем другие ошибки
            logger.warning(f"Ошибка при ответе на callback query: {e}")
    except Exception as e:
        logger.warning(f"Неожиданная ошибка при ответе на callback query: {e}")

