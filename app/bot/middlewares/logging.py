"""Middleware для логирования чатов."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services.chat_logger import chat_logger
from app.utils.user import get_user_display_name


class ChatLoggingMiddleware(BaseMiddleware):
    """Логирует все сообщения в текстовые файлы (БЕЗ отправки уведомлений админу)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка события с логированием (ТОЛЬКО в файл, БЕЗ уведомлений)."""
        result = await handler(event, data)

        if isinstance(event, Message) and event.text:
            username = get_user_display_name(event.from_user)
            chat_logger.log_message(
                user_id=event.from_user.id, username=username, message=event.text, is_bot=False
            )

        if isinstance(result, Message) and result.text:
            chat_logger.log_message(
                user_id=result.chat.id, username="БОТ", message=result.text, is_bot=True
            )

        return result
