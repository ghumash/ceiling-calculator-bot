"""Pydantic модели для расчёта стоимости."""

from pydantic import BaseModel, Field


class CalculationData(BaseModel):
    """Данные расчёта стоимости натяжного потолка."""

    # Площадь
    area: float = Field(..., gt=0, le=500, description="Площадь помещения в м²")
    area_for_calculation: float = Field(
        default=0, description="Площадь для расчёта (мин. 20м²)"
    )

    # Профиль
    profile_type: str = Field(..., description="Тип профиля: insert/shadow/floating")
    profile_cost: float = Field(default=0, description="Стоимость профиля")

    # Карнизы
    cornice_length: float = Field(default=0, ge=0, description="Длина карнизов в пог.м")
    cornice_type: str | None = Field(default=None, description="Тип карниза: pk14/pk5/bp40")
    cornice_cost: float = Field(default=0, description="Стоимость карнизов")

    # Освещение
    spotlights: int = Field(default=0, ge=0, description="Количество точечных светильников")
    spotlights_cost: float = Field(default=0, description="Стоимость установки светильников")

    # Треки
    track_type: str | None = Field(default=None, description="Тип треков: surface/built_in")
    track_length: float = Field(default=0, ge=0, description="Длина треков в м")
    track_cost: float = Field(default=0, description="Стоимость треков")

    # Световые линии
    light_lines: float = Field(default=0, ge=0, description="Длина световых линий в м")
    light_lines_cost: float = Field(default=0, description="Стоимость световых линий")

    chandeliers: int = Field(default=0, ge=0, description="Количество люстр")
    chandeliers_cost: float = Field(default=0, description="Стоимость установки люстр")

    # Чистовые работы
    wall_finish: bool = Field(default=False, description="Выполнены ли чистовые работы стен")

    # Итого
    ceiling_cost: float = Field(default=0, description="Стоимость потолка")
    total_cost: float = Field(default=0, description="Общая стоимость")
