"""Tratamento de erros centralizado — respostas padronizadas, sem vazar stack/erro interno."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify({"erro": exc.message, "sucesso": False}), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"erro": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logger.exception("Erro inesperado: %s", exc)
        return jsonify({"erro": "Erro interno"}), 500
