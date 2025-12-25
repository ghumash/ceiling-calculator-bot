"""Middleware для уведомлений админу."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class AdminNotifyMiddleware(BaseMiddleware):
    """Отправляет уведомления админам о новых расчётах."""

    def __init__(self, admin_ids: list[int]):
        """Инициализация middleware.

        Args:
            admin_ids: Список ID администраторов
        """
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка события с уведомлением админов."""
        result = await handler(event, data)

        # Уведомление при начале нового расчёта
        if isinstance(event, Message) and event.text:
            if event.text == "/start":
                await self._notify_new_calculation(event, data.get("bot"))

        return result

    async def _notify_new_calculation(self, event: Message, bot: Bot | None) -> None:
        """Отправляет уведомление админам о новом расчёте."""
        if not bot or not self.admin_ids:
            return

        try:
            from datetime import datetime

            username = event.from_user.username or event.from_user.first_name
            user_id = event.from_user.id
            date = datetime.now().strftime("%d.%m.%Y %H:%M")

            message = (
                "🔔 НОВЫЙ РАСЧЁТ\n\n"
                f"Пользователь: @{username} (ID: {user_id})\n"
                f"Дата: {date}\n"
                f"Статус: Начал диалог"
            )

            for admin_id in self.admin_ids:
                try:
                    await bot.send_message(admin_id, message)
                except Exception as e:
                    # Игнорируем ошибку, если админ не начал диалог с ботом
                    error_msg = str(e).lower()
                    if "chat not found" not in error_msg and "bot was blocked" not in error_msg:
                        logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админу: {e}")
