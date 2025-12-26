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

    # Проверка обязательных директорий
    Path("chat_logs").mkdir(exist_ok=True)
    Path("static/images/profiles").mkdir(parents=True, exist_ok=True)
    Path("static/images/cornices").mkdir(parents=True, exist_ok=True)

    # Инициализация бота
    try:
        bot = Bot(token=settings.bot_token)
    except Exception as e:
        logger.error(f"Ошибка инициализации бота: {e}")
        raise

    # Диспетчер с MemoryStorage
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение middleware
    dp.message.middleware(ChatLoggingMiddleware())
    dp.callback_query.middleware(ChatLoggingMiddleware())

    # Подключение роутеров
    dp.include_router(start.router)
    dp.include_router(calculation.router)

    logger.info("Bot started successfully!")

    # Запуск polling с обработкой сетевых ошибок
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        error_msg = str(e)
        # Сетевые ошибки не критичны - это временные проблемы с подключением
        if "Connection" in error_msg or "Network" in error_msg or "timeout" in error_msg.lower():
            logger.warning(f"Сетевая ошибка при подключении к Telegram API: {e}")
            logger.info("Проверьте интернет-соединение и доступность api.telegram.org")
        else:
            logger.error(f"Критическая ошибка при работе бота: {e}")
            raise
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
