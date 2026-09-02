"""Configuração por ambiente.

Nenhum segredo é hardcoded: `SECRET_KEY` e `ADMIN_TOKEN` são **obrigatórios** e vêm
exclusivamente do ambiente. Sem eles a aplicação falha na inicialização (fail-fast) com
mensagem clara — não existe mais fallback constante versionado.

Conveniência de desenvolvimento (explícita): com `FLASK_ENV=development`, valores
aleatórios são gerados **em memória** a cada boot (nunca uma constante no repositório).
"""
import logging
import os
import secrets

from src.errors import ConfigError

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # python-dotenv é opcional; sem ele, lê direto do ambiente
    pass

logger = logging.getLogger(__name__)

DEV_ENVS = ("development", "dev")


def _as_bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")


def _is_dev_mode():
    return os.environ.get("FLASK_ENV", "").strip().lower() in DEV_ENVS


def _required_secret(name, dev_mode):
    """Lê um segredo obrigatório do ambiente.

    Em `FLASK_ENV=development` gera um valor aleatório efêmero; fora disso levanta
    ConfigError para abortar o boot.
    """
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if dev_mode:
        generated = secrets.token_urlsafe(32)
        logger.warning(
            "%s não definida: valor aleatório gerado APENAS para FLASK_ENV=development "
            "(muda a cada boot, invalida tokens anteriores): %s",
            name, generated,
        )
        return generated
    raise ConfigError(
        f"A variável de ambiente obrigatória {name} não está definida. "
        f"Defina {name} no ambiente (veja .env.example) antes de iniciar a aplicação. "
        "Para conveniência local, use FLASK_ENV=development para gerar um valor "
        "aleatório efêmero em memória."
    )


class Settings:
    def __init__(self):
        dev_mode = _is_dev_mode()
        self.ENV = os.environ.get("FLASK_ENV", "production")
        self.SECRET_KEY = _required_secret("SECRET_KEY", dev_mode)
        self.ADMIN_TOKEN = _required_secret("ADMIN_TOKEN", dev_mode)
        self.DEBUG = _as_bool(os.environ.get("DEBUG", "false"))
        self.DB_PATH = os.environ.get("DB_PATH", "loja.db")
        self.CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
        self.HOST = os.environ.get("HOST", "0.0.0.0")
        self.PORT = int(os.environ.get("PORT", "5000"))
        # Validade do token de sessão assinado (segundos) — 24h por padrão.
        self.TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "86400"))


settings = Settings()
