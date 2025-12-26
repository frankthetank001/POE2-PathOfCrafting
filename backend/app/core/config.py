from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env (like LLM settings from feature branch)
    )

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    database_url: str = Field(default="sqlite:///./poe2tradecraft.db")
    redis_url: str = Field(default="redis://localhost:6379/0")

    cors_origins: List[str] = Field(
        default=["*"]  # Allow all origins (can be overridden via CORS_ORIGINS env var)
    )

    poeninja_base_url: str = Field(default="https://poe.ninja/api/data")
    poeninja_cache_ttl: int = Field(default=3600)

    api_v1_prefix: str = Field(default="/api/v1")

    # Security settings
    secret_key: str = Field(default="change-this-secret-key-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_days: int = Field(default=7)

    # Default admin credentials (change in production via env vars)
    default_admin_username: str = Field(default="admin")
    default_admin_password: str = Field(default="changeme")


settings = Settings()