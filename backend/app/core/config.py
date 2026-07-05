"""
Centralized application settings.

All configuration flows through this single Settings object, loaded once from
environment variables / .env at startup. Never call os.getenv() directly
elsewhere in the codebase — import `settings` from here instead. This gives us
one place to see every configurable value, and validation (via pydantic) that
fails fast at startup rather than at 2am when the pipeline runs.
"""

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    CI = "ci"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    environment: Environment = Environment.LOCAL
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+psycopg://invest:invest@localhost:5432/invest"

    # --- Data source API keys (all optional at import time; validated where used) ---
    fmp_api_key: str | None = None
    fred_api_key: str | None = None
    newsapi_key: str | None = None

    # --- Trading 212 execution ---
    # DRY_RUN defaults to True on purpose. Going live requires a deliberate,
    # explicit override — never a default.
    dry_run: bool = Field(default=True)
    t212_api_key: str | None = None
    t212_api_secret: str | None = None
    t212_use_demo: bool = Field(default=True)

    @property
    def t212_base_url(self) -> str:
        return "https://demo.trading212.com/api/v0" if self.t212_use_demo else "https://live.trading212.com/api/v0"


settings = Settings()
