from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    database_url: str = Field(default="sqlite:///./poe2tradecraft.db")
    redis_url: str = Field(default="redis://localhost:6379/0")

    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    poeninja_base_url: str = Field(default="https://poe.ninja/api/data")
    poeninja_cache_ttl: int = Field(default=3600)

    api_v1_prefix: str = Field(default="/api/v1")


settings = Settings()