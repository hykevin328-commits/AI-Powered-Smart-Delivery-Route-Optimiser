"""
Central application settings.

Tries to use pydantic-settings for full .env support.
Falls back to a plain dataclass that reads from os.environ + .env file
if pydantic-settings is not installed — so the server always starts.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

# ── Load .env manually (works without python-dotenv too) ─────────────────────
def _load_dotenv() -> None:
    """Parse a .env file and populate os.environ (only sets missing keys)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv()


# ── Try pydantic-settings; fall back to plain implementation ──────────────────
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        APP_NAME: str = "Smart Delivery Route Optimizer"
        APP_VERSION: str = "1.0.0"
        APP_ENV: str = "development"
        DEBUG: bool = False

        SECRET_KEY: str = "change-me-32-chars-minimum-secret"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        DATABASE_URL: str = ""
        SYNC_DATABASE_URL: str = ""

        SUPABASE_URL: str = ""
        SUPABASE_ANON_KEY: str = ""
        SUPABASE_SERVICE_ROLE_KEY: str = ""

        REDIS_URL: str = "redis://localhost:6379/0"

        GOOGLE_MAPS_API_KEY: str = ""
        OPENROUTESERVICE_API_KEY: str = ""
        GEOCODING_PROVIDER: str = "nominatim"

        ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

        LOG_LEVEL: str = "INFO"
        LOG_FORMAT: str = "console"

        MAX_VEHICLES: int = 50
        MAX_LOCATIONS: int = 500
        OPTIMIZATION_TIME_LIMIT_SECONDS: int = 30
        TRAFFIC_CACHE_TTL: int = 300

        @property
        def cors_origins(self) -> List[str]:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

except ModuleNotFoundError:
    # ── Fallback: plain class that reads from os.environ ─────────────────────
    import warnings
    warnings.warn(
        "pydantic-settings is not installed. Using os.environ fallback.\n"
        "Run:  \"C:\\Program Files\\Python313\\python.exe\" -m pip install pydantic-settings==2.6.1",
        stacklevel=2,
    )

    def _env(key: str, default: str = "") -> str:
        return os.environ.get(key.upper(), os.environ.get(key.lower(), default))

    def _env_int(key: str, default: int) -> int:
        try:
            return int(_env(key, str(default)))
        except ValueError:
            return default

    def _env_bool(key: str, default: bool) -> bool:
        return _env(key, str(default)).lower() in ("1", "true", "yes")

    class Settings:  # type: ignore[no-redef]
        APP_NAME:    str = _env("APP_NAME",    "Smart Delivery Route Optimizer")
        APP_VERSION: str = _env("APP_VERSION", "1.0.0")
        APP_ENV:     str = _env("APP_ENV",     "development")
        DEBUG:       bool = _env_bool("DEBUG", False)

        SECRET_KEY: str = _env("SECRET_KEY", "change-me-32-chars-minimum-secret-key!")
        ALGORITHM:  str = _env("ALGORITHM",  "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        REFRESH_TOKEN_EXPIRE_DAYS:   int = _env_int("REFRESH_TOKEN_EXPIRE_DAYS",   7)

        DATABASE_URL:      str = _env("DATABASE_URL",      "")
        SYNC_DATABASE_URL: str = _env("SYNC_DATABASE_URL", "")

        SUPABASE_URL:              str = _env("SUPABASE_URL",              "")
        SUPABASE_ANON_KEY:         str = _env("SUPABASE_ANON_KEY",         "")
        SUPABASE_SERVICE_ROLE_KEY: str = _env("SUPABASE_SERVICE_ROLE_KEY", "")

        REDIS_URL: str = _env("REDIS_URL", "redis://localhost:6379/0")

        GOOGLE_MAPS_API_KEY:       str = _env("GOOGLE_MAPS_API_KEY",       "")
        OPENROUTESERVICE_API_KEY:  str = _env("OPENROUTESERVICE_API_KEY",  "")
        GEOCODING_PROVIDER:        str = _env("GEOCODING_PROVIDER",        "nominatim")

        ALLOWED_ORIGINS: str = _env(
            "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
        )

        LOG_LEVEL:  str = _env("LOG_LEVEL",  "INFO")
        LOG_FORMAT: str = _env("LOG_FORMAT", "console")

        MAX_VEHICLES:                    int = _env_int("MAX_VEHICLES",                    50)
        MAX_LOCATIONS:                   int = _env_int("MAX_LOCATIONS",                   500)
        OPTIMIZATION_TIME_LIMIT_SECONDS: int = _env_int("OPTIMIZATION_TIME_LIMIT_SECONDS", 30)
        TRAFFIC_CACHE_TTL:               int = _env_int("TRAFFIC_CACHE_TTL",               300)

        @property
        def cors_origins(self) -> List[str]:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
