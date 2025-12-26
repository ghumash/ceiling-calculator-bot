"""Утилиты для валидации пользовательского ввода."""


def parse_float(text: str) -> float | None:
    """Парсит строку в float, заменяя запятую на точку.
    
    Args:
        text: Строка для парсинга
        
    Returns:
        Float значение или None если не удалось распарсить
    """
    try:
        return float(text.strip().replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_int(text: str) -> int | None:
    """Парсит строку в int.
    
    Args:
        text: Строка для парсинга
        
    Returns:
        Int значение или None если не удалось распарсить
    """
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return None


def validate_range(value: float, min_val: float, max_val: float) -> bool:
    """Проверяет, что значение находится в диапазоне.
    
    Args:
        value: Значение для проверки
        min_val: Минимальное значение
        max_val: Максимальное значение
        
    Returns:
        True если значение в диапазоне, иначе False
    """
    return min_val <= value <= max_val


def validate_phone(phone: str) -> bool:
    """Проверяет корректность номера телефона.
    
    Номер должен начинаться с 8 и иметь длину 11 символов.
    
    Args:
        phone: Номер телефона для проверки
        
    Returns:
        True если номер корректен, иначе False
    """
    if not phone:
        return False
    
    # Удаляем все символы кроме цифр
    cleaned = "".join(c for c in phone if c.isdigit())
    
    # Проверяем: начинается с 8 и длина 11 символов
    return len(cleaned) == 11 and cleaned.startswith("8")


def normalize_phone(phone: str) -> str:
    """Нормализует номер телефона, оставляя только цифры.
    
    Args:
        phone: Номер телефона
        
    Returns:
        Нормализованный номер (11 цифр, начинается с 8)
    """
    return "".join(c for c in phone if c.isdigit())

