"""Tratamento de erros centralizado — respostas padronizadas, sem vazar stack."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from errors import AppError

logger = logging.getLogger(__name__)


def _rollback():
    """Desfaz a transação pendente antes de responder o erro.

    Sem isto a sessão só era limpa pelo teardown do Flask-SQLAlchemy — o
    tratamento central de erros dependia de um efeito colateral externo para
    não deixar escrita parcial pendurada.
    """
    try:
        db.session.rollback()
    except Exception:  # pragma: no cover - sessão já inutilizável
        logger.exception('Falha ao desfazer a transação após erro')


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        _rollback()
        return jsonify({'error': exc.message}), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        _rollback()
        return jsonify({'error': exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        _rollback()
        logger.exception('Erro inesperado: %s', exc)
        return jsonify({'error': 'Erro interno'}), 500
