"""Точка входа для запуска бота."""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from app.core.config import settings
from app.bot.handlers import start, calculation
from app.bot.middlewares.logging import ChatLoggingMiddleware


# Загрузка .env
load_dotenv()


async def main() -> None:
    """Запуск бота."""
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting Ceiling Calculator Bot...")

    # Создание необходимых директорий
    Path("chat_logs").mkdir(exist_ok=True)

    # Инициализация бота
    bot = Bot(token=settings.bot_token)

    # Диспетчер с MemoryStorage
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение middleware
    dp.message.middleware(ChatLoggingMiddleware())
    dp.callback_query.middleware(ChatLoggingMiddleware())

    # Подключение роутеров
    dp.include_router(start.router)
    dp.include_router(calculation.router)

    logger.info("Bot started successfully!")

    # Запуск polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
