"""Application configuration. All values come from the environment or .env."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    try:
        return int(raw) if raw is not None and raw.strip() else default
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    try:
        return float(raw) if raw is not None and raw.strip() else default
    except ValueError:
        return default


def _env_date(key: str, default: str) -> date:
    raw = os.getenv(key, default)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.fromisoformat(default)


def _resolve_sqlite_url(url: str) -> str:
    """Resolve a relative SQLite path against backend/ and enforce SQLite only."""
    if not url.startswith("sqlite:"):
        raise RuntimeError("DATABASE_URL must be a sqlite: URL (SQLite only).")
    prefix = "sqlite:///"
    if url == "sqlite:///:memory:" or not url.startswith(prefix):
        return url
    raw = url[len(prefix) :]
    if not raw:
        raise RuntimeError("DATABASE_URL has an empty SQLite path.")
    if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
        return url
    resolved = (BACKEND_DIR / raw).resolve()
    return "sqlite:///" + resolved.as_posix()


def _resolve_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = (BACKEND_DIR / path).resolve()
    return str(path)


class Config:
    """Base/development configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-too")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=_env_int("JWT_ACCESS_MINUTES", 30))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=_env_int("JWT_REFRESH_DAYS", 30))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    JWT_ERROR_MESSAGE_KEY = "message"

    SQLALCHEMY_DATABASE_URI = _resolve_sqlite_url(
        os.getenv("DATABASE_URL", "sqlite:///instance/carbonwise.sqlite3")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = _env_int("PORT", 5000)
    DEBUG = _env_bool("FLASK_DEBUG", False)
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ar")
    CURRENCY = os.getenv("CURRENCY", "N/A")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    AI_DAILY_TOKEN_BUDGET = _env_int("AI_DAILY_TOKEN_BUDGET", 200000)
    AI_RATE_LIMIT_PER_HOUR = _env_int("AI_RATE_LIMIT_PER_HOUR", 20)
    AI_CACHE_TTL_MINUTES = _env_int("AI_CACHE_TTL_MINUTES", 60)
    AI_MAX_RETRIES = _env_int("AI_MAX_RETRIES", 2)
    AI_REQUEST_TIMEOUT_SECONDS = _env_int("AI_REQUEST_TIMEOUT_SECONDS", 45)
    AI_COMPLETION_TOKEN_FLOOR = _env_int("AI_COMPLETION_TOKEN_FLOOR", 4096)
    AI_REASONING_TOKEN_CAP = _env_int("AI_REASONING_TOKEN_CAP", 1024)
    AI_SCREENSHOT_MODE = _env_bool("AI_SCREENSHOT_MODE", False)

    UPLOAD_FOLDER = _resolve_path(os.getenv("UPLOAD_FOLDER", "instance/uploads"))
    MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH", 30 * 1024 * 1024)
    MAX_IMAGE_BYTES = _env_int("MAX_IMAGE_BYTES", 10 * 1024 * 1024)
    ALLOWED_IMAGE_TYPES = tuple(
        x.strip()
        for x in os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/webp").split(",")
        if x.strip()
    )
    ALLOWED_DOCUMENT_TYPES = tuple(
        x.strip()
        for x in os.getenv("ALLOWED_DOCUMENT_TYPES", "application/pdf").split(",")
        if x.strip()
    )

    ADMIN_SEED_EMAIL = os.getenv("ADMIN_SEED_EMAIL", "admin@carbonwise.demo")
    ADMIN_SEED_PASSWORD = os.getenv("ADMIN_SEED_PASSWORD", "")
    DEMO_SEED_DATE = _env_date("DEMO_SEED_DATE", "2026-06-30")
    DEMO_TODAY = _env_date("DEMO_TODAY", os.getenv("DEMO_SEED_DATE", "2026-06-30"))

    SIGNIFICANT_INCREASE_PERCENT = _env_float("SIGNIFICANT_INCREASE_PERCENT", 20.0)
    SIGNIFICANT_INCREASE_MIN_KG = _env_float("SIGNIFICANT_INCREASE_MIN_KG", 10.0)

    WTF_CSRF_TIME_LIMIT = None

    @staticmethod
    def init_app(app) -> None:
        """Validate hard stack rules and prepare folders."""
        if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
            raise RuntimeError("Only SQLite is allowed.")
        if app.config["OPENROUTER_MODEL"] != "openrouter/free":
            raise RuntimeError("OPENROUTER_MODEL must be exactly 'openrouter/free'.")
        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        Path(app.config["UPLOAD_FOLDER"]).chmod(0o700) if os.name != "nt" else None


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    OPENROUTER_API_KEY = ""
    AI_SCREENSHOT_MODE = False
    DEBUG = False
    UPLOAD_FOLDER = str(BACKEND_DIR / "instance" / "test-uploads")


class DevelopmentConfig(Config):
    DEBUG = True
