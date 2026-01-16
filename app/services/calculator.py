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


def calculate_spotlights_cost(builtin: int, surface: int, pendant: int) -> float:
    """Рассчитывает стоимость светильников по типам."""
    return (
        builtin * settings.spotlight_builtin_price +
        surface * settings.spotlight_surface_price +
        pendant * settings.spotlight_pendant_price
    )


def calculate_chandeliers_cost(chandeliers: int) -> float:
    """Рассчитывает стоимость люстр."""
    return chandeliers * settings.chandelier_price


def calculate_tracks_cost(surface_length: float, builtin_length: float) -> float:
    """Рассчитывает стоимость треков по типам."""
    return (
        surface_length * settings.track_surface_price +
        builtin_length * settings.track_built_in_price
    )


def calculate_light_lines_cost(length: float) -> float:
    """Рассчитывает стоимость световых линий."""
    return length * settings.light_lines_price if length > 0 else 0.0


def calculate_total(data: dict) -> CalculationData:
    """Выполняет полный расчёт стоимости."""
    area = data.get("area", 0.0)
    if area <= 0:
        raise ValueError("Площадь помещения не указана или некорректна")
    
    area_for_calculation, ceiling_cost = calculate_area_cost(area)

    profile_type = data.get("profile_type", "insert")
    profile_cost = calculate_profile_cost(area, profile_type)

    cornice_length = data.get("cornice_length", 0)
    cornice_type = data.get("cornice_type")
    cornice_cost = calculate_cornice_cost(cornice_length, cornice_type)

    # Светильники по типам
    spotlights_builtin = data.get("spotlights_builtin", 0)
    spotlights_surface = data.get("spotlights_surface", 0)
    spotlights_pendant = data.get("spotlights_pendant", 0)
    spotlights_cost = calculate_spotlights_cost(spotlights_builtin, spotlights_surface, spotlights_pendant)

    # Треки по типам
    track_surface_length = data.get("track_surface_length", 0)
    track_builtin_length = data.get("track_builtin_length", 0)
    track_cost = calculate_tracks_cost(track_surface_length, track_builtin_length)

    light_lines = data.get("light_lines", 0)
    light_lines_cost = calculate_light_lines_cost(light_lines)

    chandeliers = data.get("chandeliers", 0)
    chandeliers_cost = calculate_chandeliers_cost(chandeliers)

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
        spotlights_builtin=spotlights_builtin,
        spotlights_surface=spotlights_surface,
        spotlights_pendant=spotlights_pendant,
        spotlights_cost=spotlights_cost,
        track_surface_length=track_surface_length,
        track_builtin_length=track_builtin_length,
        track_cost=track_cost,
        light_lines=light_lines,
        light_lines_cost=light_lines_cost,
        chandeliers=chandeliers,
        chandeliers_cost=chandeliers_cost,
        wall_finish=wall_finish,
        ceiling_cost=ceiling_cost,
        total_cost=total_cost,
    )
