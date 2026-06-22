from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    google_safe_browsing_api_key: str = Field(default="", description="Google Safe Browsing API key")
    telegram_bot_token: str = Field(default="", description="Telegram Bot API token")
    db_path: str = Field(default="safelink.db", description="Path to SQLite database file")
    cache_ttl_seconds: int = Field(default=3600, ge=0, description="Cache TTL in seconds")
    memory_cache_max_size: int = Field(default=2048, ge=1, description="Max entries in LRU memory cache")
    check_timeout_seconds: float = Field(default=5.0, gt=0, description="Timeout for individual security checks")
    whois_timeout_seconds: float = Field(default=10.0, gt=0, description="Timeout for WHOIS lookups")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
