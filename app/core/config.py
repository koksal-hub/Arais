from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama yapılandırma modeli."""

    app_name: str = Field(default="YouTube Automation Platform")
    environment: str = Field(default="development")
    database_url: str = Field(default="sqlite:///./automation.db")
    timezone: str = Field(default="Europe/Istanbul")
    log_level: str = Field(default="INFO")
    enable_json_logs: bool = Field(default=False)
    default_locale: str = Field(default="tr_TR")
    slack_webhook_url: str | None = None
    email_from: str = Field(default="bot@example.com")

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def database_kwargs(self) -> dict[str, Any]:
        if self.database_url.startswith("sqlite"):
            return {"connect_args": {"check_same_thread": False}}
        return {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor."""

    return Settings()


__all__ = ["Settings", "get_settings"]
