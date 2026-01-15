"""Сервис расчёта стоимости натяжного потолка."""

from app.core.config import settings
from app.schemas.calculation import CalculationData


def calculate_area_cost(area: float) -> tuple[float, float]:
    """Рассчитывает стоимость потолка по площади.

    Args:
        area: Площадь помещения в м²

    Returns:
        (area_for_calculation, ceiling_cost)
    """
    # Если площадь <= 20м², считаем от 20м²
    area_for_calculation = max(area, settings.min_area_for_calculation)
    ceiling_cost = area_for_calculation * settings.ceiling_base_price

    return area_for_calculation, ceiling_cost


def calculate_profile_cost(area: float, profile_type: str) -> float:
    """Рассчитывает стоимость профиля.

    Args:
        area: Площадь помещения в м²
        profile_type: Тип профиля (insert/shadow/floating)

    Returns:
        Стоимость профиля
    """
    if profile_type == "insert":
        return 0.0

    approximate_perimeter = area * settings.perimeter_coefficient

    profile_prices = {
        "shadow": settings.profile_shadow_price,
        "floating": settings.profile_floating_price,
    }

    return approximate_perimeter * profile_prices.get(profile_type, 0)


def calculate_cornice_cost(length: float, cornice_type: str | None) -> float:
    """Рассчитывает стоимость карнизов.

    Args:
        length: Длина карнизов в пог.м
        cornice_type: Тип карниза (pk14/pk5/bp40)

    Returns:
        Стоимость карнизов
    """
    if length == 0 or not cornice_type:
        return 0.0

    cornice_prices = {
        "pk5": settings.cornice_pk5_price,
        "am1": settings.cornice_am1_price,
        "pk14": settings.cornice_pk14_price,
        "bpp": settings.cornice_bpp_price,
        "bp40": settings.cornice_bp40_price,
    }

    return length * cornice_prices.get(cornice_type, 0)


def calculate_lighting_cost(spotlights: int, chandeliers: int) -> tuple[float, float]:
    """Рассчитывает стоимость освещения.

    Args:
        spotlights: Количество точечных светильников
        chandeliers: Количество люстр

    Returns:
        (spotlights_cost, chandeliers_cost)
    """
    spotlights_cost = spotlights * settings.spotlight_price
    chandeliers_cost = chandeliers * settings.chandelier_price

    return spotlights_cost, chandeliers_cost


def calculate_total(data: dict) -> CalculationData:
    """Выполняет полный расчёт стоимости.

    Args:
        data: Словарь с данными от пользователя

    Returns:
        CalculationData с полными расчётами
    """
    # Площадь и потолок
    area = data["area"]
    area_for_calculation, ceiling_cost = calculate_area_cost(area)

    # Профиль
    profile_type = data["profile_type"]
    profile_cost = calculate_profile_cost(area, profile_type)

    # Карнизы
    cornice_length = data.get("cornice_length", 0)
    cornice_type = data.get("cornice_type")
    cornice_cost = calculate_cornice_cost(cornice_length, cornice_type)

    # Освещение
    spotlights = data.get("spotlights", 0)
    chandeliers = data.get("chandeliers", 0)
    spotlights_cost, chandeliers_cost = calculate_lighting_cost(spotlights, chandeliers)

    # Итого
    total_cost = ceiling_cost + profile_cost + cornice_cost + spotlights_cost + chandeliers_cost

    return CalculationData(
        area=area,
        area_for_calculation=area_for_calculation,
        profile_type=profile_type,
        profile_cost=profile_cost,
        cornice_length=cornice_length,
        cornice_type=cornice_type,
        cornice_cost=cornice_cost,
        spotlights=spotlights,
        spotlights_cost=spotlights_cost,
        chandeliers=chandeliers,
        chandeliers_cost=chandeliers_cost,
        ceiling_cost=ceiling_cost,
        total_cost=total_cost,
    )
