"""Конфигурация приложения через Pydantic Settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Bot
    bot_token: str = Field(..., description="Telegram Bot Token")
    admin_ids: str = Field(default="", description="Comma-separated admin IDs")

    # Application
    debug: bool = False
    log_level: str = "INFO"

    # Contact info
    contact_phone: str = "+7 (XXX) XXX-XX-XX"
    contact_telegram: str = "@your_telegram"

    # Prices - Fabric
    fabric_msd_price: int = 902
    fabric_bauf_price: int = 974

    # Prices - Profiles
    profile_insert_price: int = 0
    profile_insert_extra_corner_price: int = 103
    profile_shadow_eco_price: int = 718
    profile_shadow_eurokraab_price: int = 1435
    profile_shadow_eurokraab_corner_price: int = 492
    profile_floating_price: int = 1845
    profile_floating_corner_price: int = 492
    profile_am1_price: int = 3844

    # Prices - Cornices
    cornice_pk14_2m_price: int = 7688
    cornice_pk14_3_2m_price: int = 12300
    cornice_pk14_3_6m_price: int = 13838
    cornice_pk5_price: int = 2819
    cornice_bp40_price: int = 1282

    # Prices - Lighting
    spotlight_price: int = 513
    ceramic_price: int = 615
    chandelier_price: int = 615

    @property
    def admin_ids_list(self) -> list[int]:
        """Возвращает список ID админов."""
        if not self.admin_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_ids.split(",") if uid.strip()]


settings = Settings()

