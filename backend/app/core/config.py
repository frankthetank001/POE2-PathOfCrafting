from typing import List, Optional

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
        default=["*"]  # Allow all origins (can be overridden via CORS_ORIGINS env var)
    )

    poeninja_base_url: str = Field(default="https://poe.ninja/api/data")
    poeninja_cache_ttl: int = Field(default=3600)

    api_v1_prefix: str = Field(default="/api/v1")

    # AI Assistant (defaults to Ollama at localhost - no auth needed!)
    llm_provider: str = Field(default="ollama", description="LLM provider: 'anthropic' or 'ollama'")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key for AI assistant")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="llama3.1", description="Ollama model name")


settings = Settings()