"""Админские команды."""

import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import settings
from app.services.chat_logger import chat_logger

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом."""
    return user_id in settings.admin_ids_list


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Показывает статистику бота."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    # Подсчёт статистики из логов
    logs_dir = Path("chat_logs")
    total_users = 0
    total_calculations = 0

    if logs_dir.exists():
        for log_file in logs_dir.glob("user_*.txt"):
            total_users += 1
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "PDF-смету" in content or "ИТОГО:" in content:
                    total_calculations += 1

    stats_text = (
        "📊 СТАТИСТИКА БОТА\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"💬 Всего расчётов: {total_calculations}\n"
        f"📅 За сегодня: N/A\n\n"
        f"⏱ Средняя длительность диалога: N/A\n"
        f"✅ Завершённых расчётов: N/A"
    )

    await message.answer(stats_text)


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """Показывает историю чата с пользователем."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    # Парсинг команды: /history 123456789
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /history <user_id>")
        return

    try:
        user_id = int(parts[1])
        log_file = Path("chat_logs") / f"user_{user_id}.txt"

        if not log_file.exists():
            await message.answer(f"История для пользователя {user_id} не найдена")
            return

        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Отправка истории (Telegram ограничение 4096 символов)
        if len(content) > 4000:
            content = content[-4000:] + "\n\n... (показаны последние сообщения)"

        await message.answer(f"📜 История чата с пользователем {user_id}\n\n{content}")

    except ValueError:
        await message.answer("❌ Неверный формат user_id. Используйте: /history 123456789")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    """Рассылка сообщения всем пользователям."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    # Парсинг команды: /broadcast Текст сообщения
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    broadcast_text = parts[1]

    # Получение списка пользователей из логов
    logs_dir = Path("chat_logs")
    user_ids = set()

    if logs_dir.exists():
        for log_file in logs_dir.glob("user_*.txt"):
            try:
                user_id = int(log_file.stem.split("_")[1])
                user_ids.add(user_id)
            except (ValueError, IndexError):
                continue

    if not user_ids:
        await message.answer("❌ Пользователи не найдены")
        return

    # Отправка сообщений
    sent = 0
    failed = 0

    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, broadcast_text)
            sent += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            failed += 1

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}"
    )


@router.message(Command("prices"))
async def cmd_prices(message: Message) -> None:
    """Показывает текущие цены."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    prices_text = (
        "💰 ТЕКУЩИЕ ЦЕНЫ\n\n"
        "Полотна:\n"
        f"• MSD: {settings.fabric_msd_price} ₽/м²\n"
        f"• BAUF: {settings.fabric_bauf_price} ₽/м²\n\n"
        "Профили:\n"
        f"• Со вставкой: {settings.profile_insert_price} ₽/пог.м\n"
        f"• Теневой ЭКОНОМ: {settings.profile_shadow_eco_price} ₽/пог.м\n"
        f"• Теневой EuroKraab: {settings.profile_shadow_eurokraab_price} ₽/пог.м\n"
        f"• Парящий: {settings.profile_floating_price} ₽/пог.м\n"
        f"• AM1: {settings.profile_am1_price} ₽/пог.м\n\n"
        "Изменить цены можно через .env файл"
    )

    await message.answer(prices_text)

