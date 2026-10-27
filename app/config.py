"""Настройки приложения через pydantic-settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vk_token: str
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./translate.db"

    mymemory_url: str = "https://api.mymemory.translated.net/get"
    libretranslate_url: str = "https://translate.terraprint.co/translate"
    translate_timeout: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
