import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./callzo_metering.db"
    DATABASE_URL_SYNC: Optional[str] = None

    # Security
    WEBHOOK_SECRET: str = "callzo_test_secret_change_me"
    API_KEY: str = "callzo_internal_api_key_secure_123"

    # Application
    APP_NAME: str = "Callzo Usage Metering Service"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Retries
    MAX_RETRY_ATTEMPTS: int = 5
    INITIAL_RETRY_BACKOFF_SECONDS: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL_SYNC or self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


settings = Settings()
