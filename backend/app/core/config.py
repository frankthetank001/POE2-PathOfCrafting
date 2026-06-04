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

    # Popular-builds analysis (POE2-Builds-Scraper artifact). Fetched from
    # builds_artifact_url (GitHub raw) if set, else loaded from the local dir -
    # mirroring how pob-data is sourced. "{slug}" in the URL is replaced with the league.
    builds_artifact_url: str = Field(
        default=""  # e.g. https://raw.githubusercontent.com/<user>/POE2-Builds-Scraper/main/data/latest-{slug}.json
    )
    builds_artifact_dir: str = Field(default="source_data/builds")  # local cache / fallback
    builds_league_slug: str = Field(default="runesofaldur")
    builds_cache_ttl: int = Field(default=21600)  # 6 hours

    # Optional HTTP proxy for ONLY the PoE2 trade API client, e.g. "http://localhost:1055"
    # to route trade2 calls out a Tailscale exit node (residential IP) past Cloudflare's
    # datacenter-IP 403. Empty = direct egress (normal). Everything else stays direct.
    trade_proxy: str = Field(default="")

    api_v1_prefix: str = Field(default="/api/v1")

    # Security settings
    secret_key: str = Field(default="change-this-secret-key-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_days: int = Field(default=7)

    # Default admin credentials (change in production via env vars)
    default_admin_username: str = Field(default="admin")
    default_admin_password: str = Field(default="changeme")


settings = Settings()