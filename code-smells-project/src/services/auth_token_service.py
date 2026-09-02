"""Emissão e verificação de tokens de sessão assinados (itsdangerous).

Fica na camada de serviço: o `UsuarioService` emite o token no login e o middleware
apenas **consome** este serviço. O middleware nunca é importado por um service.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.errors import UnauthorizedError

TOKEN_SALT = "auth-token"


class AuthTokenService:
    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._max_age = max_age

    def issue(self, usuario_id):
        """Token assinado com o id do usuário (sem dados sensíveis no payload)."""
        return self._serializer.dumps({"usuario_id": usuario_id})

    def verify(self, token):
        """Devolve o `usuario_id` do token ou levanta UnauthorizedError."""
        if not token:
            raise UnauthorizedError("Token de autenticação ausente")
        try:
            data = self._serializer.loads(token, max_age=self._max_age)
        except SignatureExpired:
            raise UnauthorizedError("Token expirado")
        except BadSignature:
            raise UnauthorizedError("Token inválido")
        usuario_id = (data or {}).get("usuario_id")
        if not usuario_id:
            raise UnauthorizedError("Token inválido")
        return usuario_id
