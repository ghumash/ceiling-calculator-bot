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
    """Рассчитывает стоимость освещения."""
    return spotlights * settings.spotlight_price, chandeliers * settings.chandelier_price


def calculate_track_cost(length: float, track_type: str | None) -> float:
    """Рассчитывает стоимость треков."""
    if length == 0 or not track_type:
        return 0.0
    track_prices = {
        "surface": settings.track_surface_price,
        "built_in": settings.track_built_in_price,
    }
    return length * track_prices.get(track_type, 0)


def calculate_light_lines_cost(length: float) -> float:
    """Рассчитывает стоимость световых линий."""
    return length * settings.light_lines_price if length > 0 else 0.0


def calculate_total(data: dict) -> CalculationData:
    """Выполняет полный расчёт стоимости."""
    area = data["area"]
    area_for_calculation, ceiling_cost = calculate_area_cost(area)

    profile_type = data["profile_type"]
    profile_cost = calculate_profile_cost(area, profile_type)

    cornice_length = data.get("cornice_length", 0)
    cornice_type = data.get("cornice_type")
    cornice_cost = calculate_cornice_cost(cornice_length, cornice_type)

    spotlights = data.get("spotlights", 0)
    chandeliers = data.get("chandeliers", 0)
    spotlights_cost, chandeliers_cost = calculate_lighting_cost(spotlights, chandeliers)

    track_type = data.get("track_type")
    track_length = data.get("track_length", 0)
    track_cost = calculate_track_cost(track_length, track_type)

    light_lines = data.get("light_lines", 0)
    light_lines_cost = calculate_light_lines_cost(light_lines)

    wall_finish = data.get("wall_finish", False)

    total_cost = (
        ceiling_cost + profile_cost + cornice_cost +
        spotlights_cost + track_cost + light_lines_cost + chandeliers_cost
    )

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
        track_type=track_type,
        track_length=track_length,
        track_cost=track_cost,
        light_lines=light_lines,
        light_lines_cost=light_lines_cost,
        chandeliers=chandeliers,
        chandeliers_cost=chandeliers_cost,
        wall_finish=wall_finish,
        ceiling_cost=ceiling_cost,
        total_cost=total_cost,
    )
