"""Entry point. Mantém o comando original `python app.py` funcionando.

A montagem da aplicação fica em `src/app.py` (composition root / padrão app-factory).
"""
from src.app import create_app
from src.config.settings import settings

app = create_app()  # também serve como objeto WSGI para gunicorn (`app:app`)

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{settings.PORT}")
    print("=" * 50)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
