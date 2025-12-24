"""Сервис расчёта стоимости натяжного потолка."""

from app.core.config import settings
from app.schemas.calculation import CalculationData


def calculate_total_cost(data: CalculationData) -> dict[str, float]:
    """Рассчитывает полную стоимость натяжного потолка.

    Args:
        data: Данные расчёта

    Returns:
        Словарь с детализацией стоимости по категориям
    """
    # 1. Полотно
    if data.fabric_type == "msd":
        fabric_price_per_m2 = settings.fabric_msd_price
    elif data.fabric_type == "bauf":
        fabric_price_per_m2 = settings.fabric_bauf_price
    else:
        fabric_price_per_m2 = 0

    fabric_total = data.area * fabric_price_per_m2

    # 2. Профиль базовый
    profile_prices = {
        "insert": settings.profile_insert_price,
        "shadow_eco": settings.profile_shadow_eco_price,
        "shadow_eurokraab": settings.profile_shadow_eurokraab_price,
        "floating": settings.profile_floating_price,
        "am1": settings.profile_am1_price,
    }

    profile_price_per_m = profile_prices.get(data.profile_type, 0)
    profile_base = data.perimeter * profile_price_per_m

    # 3. Дополнительные углы
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

    # 4. Карнизы
    cornice_total = 0.0
    if data.has_cornices and data.cornice_type:
        if data.cornice_type == "pk14_2m":
            cornice_total = settings.cornice_pk14_2m_price
        elif data.cornice_type == "pk14_3_2m":
            cornice_total = settings.cornice_pk14_3_2m_price
        elif data.cornice_type == "pk14_3_6m":
            cornice_total = settings.cornice_pk14_3_6m_price
        elif data.cornice_type == "pk5" and data.cornice_length:
            cornice_total = data.cornice_length * settings.cornice_pk5_price
        elif data.cornice_type == "bp40" and data.cornice_length:
            cornice_total = data.cornice_length * settings.cornice_bp40_price

    # 5. Освещение
    spotlights_total = data.spotlights * settings.spotlight_price
    ceramic_total = data.ceramic_area * settings.ceramic_price
    chandeliers_total = data.chandeliers * settings.chandelier_price
    lighting_total = spotlights_total + ceramic_total + chandeliers_total

    # ИТОГО
    total_cost = (
        fabric_total
        + profile_total
        + cornice_total
        + lighting_total
    )

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

