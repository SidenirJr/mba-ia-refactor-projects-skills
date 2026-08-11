"""Tratamento de erros centralizado — respostas padronizadas, sem vazar stack."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return jsonify({'error': exc.message}), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({'error': exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logger.exception('Erro inesperado: %s', exc)
        return jsonify({'error': 'Erro interno'}), 500
