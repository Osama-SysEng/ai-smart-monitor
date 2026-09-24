from functools import lru_cache
from secrets import token_urlsafe
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "The Smart Monitor"
    version: str = "4.0.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "sqlite:///./smart_monitor.db"
    database_pool_size: int = Field(default=20, ge=1, le=200)
    database_max_overflow: int = Field(default=20, ge=0, le=200)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60, le=86_400)
    redis_url: str = "redis://localhost:6379/0"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    ai_provider: str = "mock"
    ai_model: str = "gpt-4o-mini"
    ai_timeout: int = Field(default=30, ge=1, le=120)
    openai_api_key: str = ""
    erp_base_url: str = ""
    erp_api_key: str = ""
    erp_timeout: int = Field(default=20, ge=1, le=90)
    erp_max_attempts: int = Field(default=8, ge=1, le=50)
    erp_base_retry_seconds: int = Field(default=30, ge=1, le=86_400)
    erp_circuit_failure_threshold: int = Field(default=5, ge=1, le=100)
    erp_circuit_cooldown_seconds: int = Field(default=300, ge=10, le=86_400)
    cors_origins: str = "http://localhost:5173"
    require_api_key: bool = False
    api_key: str = ""
    auth_mode: Literal["legacy_api_key", "service_accounts"] = "legacy_api_key"
    session_secret: str = Field(default_factory=lambda: token_urlsafe(48))
    session_ttl_minutes: int = Field(default=30, ge=5, le=720)
    rate_limit_per_minute: int = Field(default=120, ge=10, le=100_000)
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1_024, le=250 * 1024 * 1024)
    max_import_rows: int = Field(default=100_000, ge=1, le=1_000_000)
    max_error_details: int = Field(default=500, ge=10, le=10_000)
    reconciliation_pairs: str = "warehouse:branch,branch:cost,warehouse:cost,warehouse:erp,cost:erp,branch:erp"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def reconciliation_pair_list(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for item in self.reconciliation_pairs.split(","):
            left, separator, right = item.strip().lower().partition(":")
            if separator and left and right and left != right:
                pairs.append((left, right))
        return pairs

    @model_validator(mode="after")
    def validate_production_contract(self):
        if self.environment == "production":
            if not self.require_api_key:
                raise ValueError("Production requires REQUIRE_API_KEY=true")
            if self.auth_mode == "legacy_api_key" and len(self.api_key) < 24:
                raise ValueError("Production legacy API-key mode requires a strong API_KEY")
            if self.auth_mode == "service_accounts" and "session_secret" not in self.model_fields_set:
                raise ValueError("Production service-account mode requires an explicit SESSION_SECRET")
            if not self.cors_origin_list or "*" in self.cors_origin_list:
                raise ValueError("Production requires explicit CORS origins")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production requires a server database, not SQLite")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
