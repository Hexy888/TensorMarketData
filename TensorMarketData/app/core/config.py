"""
Configuration management using Pydantic BaseSettings.
Loads environment variables automatically.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    supabase_url: str = "https://your-project.supabase.co"
    supabase_key: str = "your-service-role-key"
    database_url: str = "postgresql+asyncpg://user:password@host:5432/dbname"

    # Vector Search
    vector_size: int = 1536

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Security
    api_key_header: str = "X-API-Key"
    credits_per_search: int = 1

    # Stripe (Future)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached settings instance.
    Use this function to access settings throughout the application.
    """
    return Settings()


# Global settings instance
settings = get_settings()
