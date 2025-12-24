"""Middleware для логирования чатов."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services.chat_logger import chat_logger

logger = logging.getLogger(__name__)


class ChatLoggingMiddleware(BaseMiddleware):
    """Логирует все сообщения в текстовые файлы."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события с логированием."""
        if isinstance(event, Message) and event.text:
            username = event.from_user.username or event.from_user.first_name
            chat_logger.log_message(
                user_id=event.from_user.id,
                username=username,
                message=event.text,
                is_bot=False
            )

        return await handler(event, data)

