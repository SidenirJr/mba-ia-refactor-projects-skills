"""Configuração por ambiente — sem segredos hardcoded (lê de .env opcional em dev)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _as_bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = _as_bool(os.environ.get("DEBUG", "false"))
    DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///tasks.db")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "86400"))
    # SMTP (antes hardcoded no notification_service)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


settings = Settings()
