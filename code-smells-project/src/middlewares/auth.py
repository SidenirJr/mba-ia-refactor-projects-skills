"""Guard de autenticação para endpoints administrativos."""
from functools import wraps

from flask import jsonify, request

from src.config.settings import settings


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if not token or token != settings.ADMIN_TOKEN:
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)

    return wrapper
