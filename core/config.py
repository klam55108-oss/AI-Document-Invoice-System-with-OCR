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
    LLM_MODEL: str = "deepseek-chat"
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_TEMPERATURE: float = 0.0

    # DeepSeek Chat Settings
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TEMPERATURE: float = 0.0

    # Chatbot Settings
    CHATBOT_RATE_LIMIT: int = 20  # queries per minute
    CHATBOT_SESSION_TIMEOUT: int = 1800  # 30 minutes in seconds
    CHATBOT_MAX_RESULTS: int = 50  # maximum invoices per response
    CHATBOT_CONTEXT_WINDOW: int = 10  # last N messages in context

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
