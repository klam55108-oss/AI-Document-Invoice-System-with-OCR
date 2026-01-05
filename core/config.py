"""Configuration management using Pydantic Settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    API_TITLE: str = "E-Invoice Processing API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Database
    DATABASE_URL: str | None = None

    # Storage
    DATA_DIR: str = "data"

    # Security
    ENCRYPTION_KEY: str | None = None

    # LLM Settings
    OPENAI_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o"
    EMBED_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
