"""Guards de autenticação e autorização (Playbook P13).

O usuário é recarregado do banco em cada request: token de conta apagada ou
desativada deixa de valer na hora, em vez de continuar válido até expirar.
"""
from functools import wraps

from flask import g, request

from database import db
from errors import ForbiddenError, UnauthorizedError
from models.user import User
from services.token_service import TokenService

token_service = TokenService()


def _authenticate():
    header = request.headers.get('Authorization', '')
    token = header[7:] if header.startswith('Bearer ') else header
    if not token:
        raise UnauthorizedError('Token de autenticação ausente')
    user = db.session.get(User, token_service.read_user_id(token))
    if not user:
        raise UnauthorizedError('Sessão inválida')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    g.current_user = user
    g.current_user_id = user.id
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        _authenticate()
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not _authenticate().is_admin():
            raise ForbiddenError('Requer privilégio de administrador')
        return f(*args, **kwargs)
    return wrapper


def current_user():
    """Usuário autenticado do request corrente — os controllers repassam este
    valor aos services, que não conhecem `flask.g`."""
    return getattr(g, 'current_user', None)
