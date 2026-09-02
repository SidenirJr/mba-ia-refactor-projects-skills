"""Emissão e leitura dos tokens de sessão assinados.

Mora em `services/` de propósito: antes o `user_service` importava
`middlewares.auth._serializer`, ou seja, a camada de negócio dependia da camada
HTTP — e ainda por uma função privada. Aqui a dependência aponta na direção
correta: o middleware consome o service.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.settings import settings
from errors import UnauthorizedError

TOKEN_SALT = 'auth-token'


class TokenService:
    def _serializer(self):
        return URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)

    def generate(self, user_id):
        return self._serializer().dumps({'user_id': user_id})

    def read_user_id(self, token):
        try:
            data = self._serializer().loads(token, max_age=settings.TOKEN_MAX_AGE)
        except (BadSignature, SignatureExpired):
            raise UnauthorizedError('Token inválido ou expirado')
        user_id = (data or {}).get('user_id')
        if not user_id:
            raise UnauthorizedError('Token inválido ou expirado')
        return user_id
