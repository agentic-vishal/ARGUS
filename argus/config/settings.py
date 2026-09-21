"""Validated environment-backed settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ARGUS"
    environment: str = "development"
    log_level: str = "INFO"
    log_json: bool = False
    max_investigation_iterations: int = Field(default=5, ge=1, le=100)
    min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    research_timeout_seconds: float = Field(default=30.0, gt=0.0)
    mcp_timeout_seconds: float = Field(default=10.0, gt=0.0, le=120.0)
    mcp_max_retries: int = Field(default=2, ge=0, le=10)
    mcp_retry_backoff_seconds: float = Field(default=0.25, ge=0.0, le=30.0)
    news_mcp_url: str | None = None
    government_mcp_url: str | None = None
    market_mcp_url: str | None = None
    company_mcp_url: str | None = None
    react_max_iterations: int = Field(default=8, ge=1, le=100)
    react_max_tool_calls: int = Field(default=8, ge=1, le=100)
    cascade_max_fallbacks: int = Field(default=2, ge=0, le=3)

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("log_level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        return normalized


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
