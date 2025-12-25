"""Сервис расчёта стоимости натяжного потолка."""

from app.core.config import settings
from app.schemas.calculation import CalculationData


def _calculate_fabric_cost(data: CalculationData) -> float:
    """Рассчитывает стоимость полотна.

    Args:
        data: Данные расчёта

    Returns:
        Стоимость полотна
    """
    if data.fabric_type == "msd":
        price_per_m2 = settings.fabric_msd_price
    elif data.fabric_type == "bauf":
        price_per_m2 = settings.fabric_bauf_price
    else:
        price_per_m2 = 0

    return data.area * price_per_m2


def _calculate_profile_cost(data: CalculationData) -> tuple[float, float, float]:
    """Рассчитывает стоимость профиля и углов.

    Args:
        data: Данные расчёта

    Returns:
        Кортеж (базовая стоимость профиля, стоимость углов, общая стоимость профиля)
    """
    profile_prices = {
        "insert": settings.profile_insert_price,
        "shadow_eco": settings.profile_shadow_eco_price,
        "shadow_eurokraab": settings.profile_shadow_eurokraab_price,
        "floating": settings.profile_floating_price,
        "am1": settings.profile_am1_price,
    }

    profile_price_per_m = profile_prices.get(data.profile_type, 0)
    profile_base = data.perimeter * profile_price_per_m

    corners_total = 0.0
    if data.profile_type == "insert":
        extra_corners = max(0, data.corners - 4)
        corners_total = extra_corners * settings.profile_insert_extra_corner_price
    elif data.profile_type in ["shadow_eurokraab", "floating"]:
        corner_price = (
            settings.profile_shadow_eurokraab_corner_price
            if data.profile_type == "shadow_eurokraab"
            else settings.profile_floating_corner_price
        )
        corners_total = data.corners * corner_price

    profile_total = profile_base + corners_total
    return profile_base, corners_total, profile_total


def _calculate_cornice_cost(data: CalculationData) -> float:
    """Рассчитывает стоимость карниза.

    Args:
        data: Данные расчёта

    Returns:
        Стоимость карниза
    """
    if not data.has_cornices or not data.cornice_type:
        return 0.0

    if data.cornice_type == "pk14_2m":
        return settings.cornice_pk14_2m_price
    elif data.cornice_type == "pk14_3_2m":
        return settings.cornice_pk14_3_2m_price
    elif data.cornice_type == "pk14_3_6m":
        return settings.cornice_pk14_3_6m_price
    elif data.cornice_type == "pk5" and data.cornice_length:
        return data.cornice_length * settings.cornice_pk5_price
    elif data.cornice_type == "bp40" and data.cornice_length:
        return data.cornice_length * settings.cornice_bp40_price

    return 0.0


def _calculate_lighting_cost(data: CalculationData) -> tuple[float, float, float, float]:
    """Рассчитывает стоимость освещения.

    Args:
        data: Данные расчёта

    Returns:
        Кортеж (стоимость светильников, керамогранита, люстр, общая стоимость освещения)
    """
    spotlights_total = data.spotlights * settings.spotlight_price
    ceramic_total = data.ceramic_area * settings.ceramic_price
    chandeliers_total = data.chandeliers * settings.chandelier_price
    lighting_total = spotlights_total + ceramic_total + chandeliers_total

    return spotlights_total, ceramic_total, chandeliers_total, lighting_total


def calculate_total_cost(data: CalculationData) -> dict[str, float]:
    """Рассчитывает полную стоимость натяжного потолка.

    Args:
        data: Данные расчёта

    Returns:
        Словарь с детализацией стоимости по категориям
    """
    fabric_total = _calculate_fabric_cost(data)
    profile_base, corners_total, profile_total = _calculate_profile_cost(data)
    cornice_total = _calculate_cornice_cost(data)
    spotlights_total, ceramic_total, chandeliers_total, lighting_total = _calculate_lighting_cost(
        data
    )

    total_cost = fabric_total + profile_total + cornice_total + lighting_total

    return {
        "fabric_total": fabric_total,
        "profile_base": profile_base,
        "corners_total": corners_total,
        "profile_total": profile_total,
        "cornice_total": cornice_total,
        "spotlights_total": spotlights_total,
        "ceramic_total": ceramic_total,
        "chandeliers_total": chandeliers_total,
        "lighting_total": lighting_total,
        "total_cost": total_cost,
    }
