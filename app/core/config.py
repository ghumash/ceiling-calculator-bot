"""Конфигурация приложения через Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Bot
    bot_token: str = Field(..., description="Telegram Bot Token")
    admin_ids: str = Field(default="", description="Comma-separated admin IDs")
    group_chat_id: str = Field(default="", description="Group chat ID for notifications")
    channel_chat_id: str = Field(default="", description="Channel chat ID for notifications")

    # Application
    log_level: str = "INFO"

    # Contact info
    contact_phone: str = Field(..., description="Контактный телефон менеджера")
    contact_telegram: str = Field(..., description="Telegram контакт менеджера")

    # Цены - Базовый потолок MSD
    ceiling_base_price: int = 902
    min_area_for_calculation: int = 20

    # Цены - Профили (за погонный метр)
    profile_shadow_price: int = 718
    profile_floating_price: int = 1845

    # Коэффициент для расчёта периметра от площади
    perimeter_coefficient: float = 1.5

    # Цены - Карнизы (за погонный метр)
    cornice_pk14_price: int = 3844
    cornice_pk5_price: int = 2819
    cornice_bp40_price: int = 1282

    # Цены - Освещение (за штуку)
    spotlight_price: int = 513
    chandelier_price: int = 550

    # Валидация
    max_cornice_length: float = 100.0
    max_count: int = 100

    # Пути к изображениям
    profiles_dir: str = "static/images/profiles"
    cornices_dir: str = "static/images/cornices"

    @property
    def admin_ids_list(self) -> list[int]:
        """Возвращает список ID админов (deprecated, используйте group_chat_id)."""
        if not self.admin_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_ids.split(",") if uid.strip()]

    @property
    def notification_chat_id(self) -> int | None:
        """Возвращает chat_id для отправки уведомлений (группа или первый админ).
        
        Returns:
            Chat ID для уведомлений или None
        """
        # Приоритет у group_chat_id
        if self.group_chat_id:
            return int(self.group_chat_id)
        # Fallback на первого админа из списка
        if self.admin_ids_list:
            return self.admin_ids_list[0]
        return None


settings = Settings()
