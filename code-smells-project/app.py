"""Entry point. Mantém o comando original `python app.py` funcionando.

A montagem da aplicação fica em `src/app.py` (composition root / padrão app-factory).
Se a configuração obrigatória (`SECRET_KEY`, `ADMIN_TOKEN`) estiver ausente, a subida é
abortada com mensagem clara — não há fallback de segredo no código.
"""
import sys

from src.errors import ConfigError

try:
    from src.app import create_app
    from src.config.settings import settings

    app = create_app()  # também serve como objeto WSGI para gunicorn (`app:app`)
except ConfigError as exc:
    print(f"ERRO DE CONFIGURAÇÃO: {exc}", file=sys.stderr)
    raise SystemExit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{settings.PORT}")
    print("=" * 50)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
