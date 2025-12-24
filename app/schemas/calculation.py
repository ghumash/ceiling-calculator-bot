"""Pydantic модели для расчёта стоимости."""

from pydantic import BaseModel, Field


class CalculationData(BaseModel):
    """Данные расчёта стоимости натяжного потолка."""

    # Базовые параметры
    area: float = Field(..., ge=5, le=200, description="Площадь помещения в м²")
    corners: int = Field(..., ge=4, description="Количество углов")
    perimeter: float = Field(..., gt=0, description="Периметр помещения в пог.м")

    # Материалы
    fabric_type: str = Field(..., description="Тип полотна: 'msd' или 'bauf'")
    profile_type: str = Field(..., description="Тип профиля")

    # Карнизы
    has_cornices: bool = Field(default=False, description="Нужны ли карнизы")
    cornice_type: str | None = Field(default=None, description="Тип карниза")
    cornice_length: float | None = Field(default=None, ge=0, description="Длина карниза в пог.м")

    # Освещение
    spotlights: int = Field(default=0, ge=0, description="Количество точечных светильников")
    has_ceramic: bool = Field(default=False, description="Есть ли керамогранит")
    ceramic_area: float = Field(default=0, ge=0, description="Площадь керамогранита в пог.м")
    chandeliers: int = Field(default=0, ge=0, description="Количество люстр")

