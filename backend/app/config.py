from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="INSPECTION_", extra="ignore"
    )

    app_name: str = "Inspection System API"
    version: str = "0.1.0"

    database_url: str = "sqlite:///./inspection.db"

    ai_service_url: str = "http://localhost:8001"
    ai_timeout_seconds: float = 5.0
    ai_enabled: bool = True

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
