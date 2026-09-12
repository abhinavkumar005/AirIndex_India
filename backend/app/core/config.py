"""
Application settings for AirIndex India.

Reads runtime configuration from environment variables (optionally via a
local `.env` file, which is never committed). Non-secret domain and
prototype configuration lives in version-controlled YAML under `configs/`.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime service settings.

    Attributes:
        environment: Deployment environment name (development, production).
        log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR).
        database_url: SQLAlchemy URL for the PostgreSQL system of record.
        redis_url: Redis URL for the broker/cache.
        api_base_url: Public base URL of the API service.
        cors_origins: Comma-separated list of allowed CORS origins.
            An empty value means "no cross-origin access" (fail closed);
            the wildcard "*" is only permitted when explicitly configured
            and credentials are then disabled.
        admin_auth_enabled: Whether administrative endpoints require auth.
        enable_real_source_collection: Global kill-switch for real-source
            collection. Must remain false until source authorizations are
            recorded (ADR-005).
        default_source_rate_limit_per_minute: Fallback rate limit for
            sources without an explicit configured limit.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+psycopg://airindex:change-me@localhost:5432/airindex"
    )
    redis_url: str = "redis://localhost:6379/0"
    api_base_url: str = "http://localhost:8000"

    cors_origins: str = "http://localhost:5173"

    admin_auth_enabled: bool = False
    secret_key: str = "replace-with-a-secret-outside-version-control"

    enable_real_source_collection: bool = False
    default_source_rate_limit_per_minute: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse `cors_origins` into a list of allowed origins.

        An empty/blank value yields an empty list (no CORS headers),
        which is the safe fail-closed default.
        """
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def allow_credentials(self) -> bool:
        """Credentials are only allowed for an explicit origin list.

        `allow_origins=["*"]` combined with `allow_credentials=True` is
        an unsafe combination that browsers reject; fail closed instead.
        """
        return bool(self.cors_origin_list) and "*" not in self.cors_origin_list


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
