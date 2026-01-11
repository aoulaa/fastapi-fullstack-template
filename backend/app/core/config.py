import os
from enum import Enum

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application metadata settings."""

    APP_NAME: str = "FastAPI Fullstack Boilerplate"
    APP_DESCRIPTION: str | None = (
        "A production-ready FastAPI boilerplate with authentication, database, and async task queue."
    )
    APP_VERSION: str | None = "0.1.0"
    LICENSE_NAME: str | None = "MIT"
    CONTACT_NAME: str | None = "Olimbek Nizomov"
    CONTACT_EMAIL: str | None = "nizomov.olimbek@gmail.com"


class CryptSettings(BaseSettings):
    """JWT and cryptography settings."""

    SECRET_KEY: SecretStr = SecretStr("secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
    POSTGRES_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        """Construct PostgreSQL connection URI from components."""
        credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"


class FirstUserSettings(BaseSettings):
    """First admin user credentials."""

    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"


class RedisSettings(BaseSettings):
    """
    Redis configuration used for caching, queues, and rate limiting.
    By default, everything uses the same Redis instance.
    """

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # To use separate Redis instances for different features, you can add
    # separate URLs here (e.g., REDIS_CACHE_URL, REDIS_QUEUE_URL) and
    # update the initialization logic in 'app/core/setup.py'.

    # Feature Toggles
    ENABLE_REDIS_QUEUE: bool = True
    ENABLE_REDIS_RATE_LIMIT: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


class DefaultRateLimitSettings(BaseSettings):
    """Default rate limiting configuration values."""

    DEFAULT_RATE_LIMIT_LIMIT: int = 10
    DEFAULT_RATE_LIMIT_PERIOD: int = 3600


class EnvironmentOption(str, Enum):
    """Environment types for the application."""

    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    """Environment configuration."""

    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


class CORSSettings(BaseSettings):
    """CORS (Cross-Origin Resource Sharing) configuration."""

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    CORS_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_HEADERS: list[str] = ["*"]


class Settings(
    AppSettings,
    DatabaseSettings,
    CryptSettings,
    FirstUserSettings,
    RedisSettings,
    DefaultRateLimitSettings,
    EnvironmentSettings,
    CORSSettings,
):
    """Combined application settings."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
