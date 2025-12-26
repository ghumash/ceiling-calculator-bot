"""Утилиты для работы с пользователями."""

from aiogram.types import User


def get_user_display_name(user: User) -> str:
    """Возвращает отображаемое имя пользователя.
    
    Args:
        user: Объект пользователя Telegram
        
    Returns:
        Username или first_name, или "Пользователь" если ничего нет
    """
    return user.username or user.first_name or "Пользователь"

