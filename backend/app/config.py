"""
Centralized application configuration.

All environment-driven settings live here so the rest of the app never
reads os.environ directly. Values are loaded from the .env file at the
project root (see backend/.env).
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database -----------------------------------------------------
    DATABASE_URL: str = "postgresql://sanik@localhost:5432/sitesafe"

    # --- Auth -----------------------------------------------------------
    # Override in .env for any real deployment — this default is only so
    # the app doesn't crash on a fresh checkout.
    JWT_SECRET_KEY: str = "MySiteSafeSecretKey2026!@#-"

    # --- App info -------------------------------------------------------
    APP_NAME: str = "Construction Safety AI"
    APP_VERSION: str = "1.0"
    ENV: str = "development"

    # --- CORS (comma separated list of allowed frontend origins) -------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Defaults used to seed the singleton Settings row --------------
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so we parse the .env file only once."""
    return Settings()


settings = get_settings()
