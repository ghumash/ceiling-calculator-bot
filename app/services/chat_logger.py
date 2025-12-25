"""Сервис логирования чатов в текстовые файлы."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class ChatLogger:
    """Логирует сообщения чата в текстовые файлы."""

    def __init__(self, logs_dir: str = "chat_logs"):
        """Инициализация логгера.

        Args:
            logs_dir: Директория для логов
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_message(
        self, user_id: int, username: Optional[str], message: str, is_bot: bool = False
    ) -> None:
        """Логирует сообщение в файл.

        Args:
            user_id: ID пользователя
            username: Имя пользователя
            message: Текст сообщения
            is_bot: Является ли отправитель ботом
        """
        try:
            # Убеждаемся, что директория существует
            self.logs_dir.mkdir(parents=True, exist_ok=True)

            log_file = self.logs_dir / f"user_{user_id}.txt"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sender = "🤖 БОТ" if is_bot else f"👤 {username or f'user_{user_id}'}"

            # Запись в файл
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {sender}: {message}\n")
        except Exception as e:
            logger.error(f"Ошибка логирования: {e}")

    def clear_chat_history(self, user_id: int) -> None:
        """Очищает историю чата пользователя (удаляет файл лога).

        Args:
            user_id: ID пользователя
        """
        log_file = self.logs_dir / f"user_{user_id}.txt"
        if log_file.exists():
            log_file.unlink()


# Глобальный экземпляр
chat_logger = ChatLogger()
