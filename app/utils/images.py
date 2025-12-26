"""Утилиты для работы с изображениями."""

import logging
from pathlib import Path

from aiogram.types import FSInputFile, Message

logger = logging.getLogger(__name__)


async def send_image_if_exists(
    message: Message, image_path: Path, fallback_paths: list[str] | None = None
) -> None:
    """Отправляет изображение, если оно существует, иначе пробует fallback.
    
    Args:
        message: Сообщение для отправки фото
        image_path: Основной путь к изображению
        fallback_paths: Список альтернативных путей для поиска
    """
    if image_path.exists():
        try:
            await message.answer_photo(photo=FSInputFile(image_path))
        except Exception as e:
            logger.error(f"Не удалось отправить изображение {image_path}: {e}")
        return

    if fallback_paths:
        for fallback_name in fallback_paths:
            fallback_path = image_path.parent / fallback_name
            if fallback_path.exists():
                try:
                    await message.answer_photo(photo=FSInputFile(fallback_path))
                except Exception as e:
                    logger.error(f"Не удалось отправить изображение {fallback_path}: {e}")
                return

