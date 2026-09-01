"""Guard de autenticação para rotas que exigem usuário logado (Playbook P13)."""
from functools import wraps

from flask import g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.settings import settings
from errors import UnauthorizedError


def _serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt='auth-token')


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        token = header[7:] if header.startswith('Bearer ') else header
        if not token:
            raise UnauthorizedError('Token de autenticação ausente')
        try:
            data = _serializer().loads(token, max_age=settings.TOKEN_MAX_AGE)
        except (BadSignature, SignatureExpired):
            raise UnauthorizedError('Token inválido ou expirado')
        g.current_user_id = data['user_id']
        return f(*args, **kwargs)
    return wrapper
