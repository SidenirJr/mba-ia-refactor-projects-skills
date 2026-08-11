"""Configuração por ambiente. Nenhum segredo é hardcoded no código de negócio:
tudo vem de variáveis de ambiente (carregadas de um .env opcional em dev)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # python-dotenv é opcional; sem ele, lê direto do ambiente
    pass


def _as_bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = _as_bool(os.environ.get("DEBUG", "false"))
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "dev-admin-token-change-me")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))


settings = Settings()
