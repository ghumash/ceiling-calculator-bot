"""Точка входа для запуска бота."""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramConflictError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
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
    Path(settings.profiles_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.cornices_dir).mkdir(parents=True, exist_ok=True)

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

    # Удаление webhook перед запуском polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удалён")

    # Проверка доступности бота перед запуском polling
    try:
        bot_info = await bot.get_me()
        logger.info(f"Бот подключён: @{bot_info.username} ({bot_info.first_name})")
    except Exception as e:
        logger.error(f"Не удалось подключиться к Telegram API: {e}")
        await bot.session.close()
        raise

    # Установка команд бота (всплывающее меню)
    commands = [
        BotCommand(command="start", description="Начать новый расчёт"),
        BotCommand(command="edit", description="Изменить параметры расчёта"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Команды бота установлены")

    logger.info("Запуск polling...")

    # Запуск polling с обработкой ошибок
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    except TelegramConflictError as e:
        error_msg = str(e)
        if "terminated by other getUpdates" in error_msg or "only one bot instance" in error_msg:
            logger.error("")
            logger.error("=" * 60)
            logger.error("ОШИБКА: Уже запущен другой экземпляр бота!")
            logger.error("=" * 60)
            logger.error("")
            logger.info("Остановите другие запущенные экземпляры бота и попробуйте снова.")
            logger.info("")
            logger.info("Проверьте процессы:")
            logger.info("  macOS/Linux: ps aux | grep python")
            logger.info("  Windows: tasklist | findstr python")
            logger.info("")
            logger.info("Или проверьте screen/tmux сессии:")
            logger.info("  screen -ls  или  tmux ls")
            logger.error("")
            logger.error("=" * 60)
            logger.error("")
            # Выходим без raise, чтобы бот корректно остановился
            return
        else:
            logger.error(f"Конфликт при работе бота: {e}")
            raise
    except Exception as e:
        error_msg = str(e)
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
