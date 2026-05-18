# config.py — Pydantic BaseSettings reads from .env automatically
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Type-safe configuration loaded from .env file."""

    # Application
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///./launchradar.db"

    # Scraping behaviour
    scrape_interval_hours: int = 24
    default_keyword: str = "startup"
    default_region: str = ""

    # API Keys
    gemini_api_key: str = ""
    eventbrite_api_key: str = ""

    # Alerts
    alert_webhook_url: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (loaded once at startup)."""
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
