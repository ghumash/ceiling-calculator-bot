"""Сервис логирования чатов в текстовые файлы."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class ChatLogger:
    """Логирует сообщения чата в текстовые файлы и накапливает их в памяти."""

    def __init__(self, logs_dir: str = "chat_logs"):
        """Инициализация логгера.

        Args:
            logs_dir: Директория для логов
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # Хранилище сообщений в памяти: {user_id: [{"timestamp": str, "sender": str, "message": str}, ...]}
        self._chat_history: dict[int, list[dict[str, str]]] = {}

    def log_message(
        self,
        user_id: int,
        username: Optional[str],
        message: str,
        is_bot: bool = False
    ) -> None:
        """Логирует сообщение в файл и накапливает в памяти.

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
            
            # Накопление в памяти
            if user_id not in self._chat_history:
                self._chat_history[user_id] = []
            
            self._chat_history[user_id].append({
                "timestamp": timestamp,
                "sender": sender,
                "message": message
            })
        except Exception as e:
            logger.error(f"Ошибка логирования: {e}")

    def get_chat_history(self, user_id: int) -> str:
        """Возвращает весь чат пользователя в виде строки.

        Args:
            user_id: ID пользователя

        Returns:
            Строка с историей чата
        """
        if user_id not in self._chat_history:
            return ""
        
        lines = []
        for entry in self._chat_history[user_id]:
            lines.append(f"[{entry['timestamp']}] {entry['sender']}: {entry['message']}")
        
        return "\n".join(lines)

    def clear_chat_history(self, user_id: int) -> None:
        """Очищает историю чата пользователя из памяти.

        Args:
            user_id: ID пользователя
        """
        if user_id in self._chat_history:
            del self._chat_history[user_id]


# Глобальный экземпляр
chat_logger = ChatLogger()

