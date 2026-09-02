"""Configuração por ambiente — sem segredos hardcoded (lê de .env opcional em dev)."""
import os
import secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _as_bool(value):
    return str(value).lower() in ("1", "true", "yes", "on")


def _required_secret(name):
    """Segredo obrigatório: sem valor no ambiente, a aplicação NÃO sobe.

    Um default constante versionado no repositório é pior do que nenhum default:
    aqui o `SECRET_KEY` assina os tokens de sessão, então quem tivesse acesso ao
    código poderia forjar a sessão de qualquer usuário. Em desenvolvimento,
    `FLASK_ENV=development` gera uma chave efêmera em memória — as sessões caem a
    cada boot, mas nenhum segredo previsível entra no código.
    """
    value = os.environ.get(name)
    if value:
        return value
    if os.environ.get("FLASK_ENV", "").lower() == "development":
        return secrets.token_urlsafe(32)
    raise RuntimeError(
        f"{name} não está definida no ambiente. Defina-a antes de subir a aplicação "
        f"(veja .env.example). Para desenvolvimento local, use FLASK_ENV=development "
        f"para gerar uma chave efêmera automaticamente."
    )


class Settings:
    SECRET_KEY = _required_secret("SECRET_KEY")
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
