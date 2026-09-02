"""Guards de autenticação/autorização.

Três guards, combináveis:
  * `login_required`      — exige token de sessão válido (401);
  * `admin_required`      — login + `tipo == 'admin'` (403 se logado sem permissão);
  * `admin_token_required` — exige o header `X-Admin-Token` (401).

O usuário é recarregado do banco a cada requisição (usuário deletado perde o acesso na
hora) e exposto em `flask.g.current_user`. O middleware apenas consome o
`AuthTokenService`; a emissão do token mora na camada de serviço.
"""
from functools import wraps

from flask import g, request

from src.config.settings import settings
from src.errors import ForbiddenError, UnauthorizedError

ADMIN_TIPO = "admin"


def _token_from_request():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return header.strip()


def admin_token_required(view):
    """Header `X-Admin-Token` (mantém o contrato original dos endpoints /admin/*)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if not token or token != settings.ADMIN_TOKEN:
            raise UnauthorizedError("Não autorizado")
        return view(*args, **kwargs)

    return wrapper


class AuthGuards:
    """Fábrica de guards — recebe as dependências por injeção (sem singletons)."""

    def __init__(self, auth_token_service, usuario_repo):
        self._tokens = auth_token_service
        self._usuarios = usuario_repo

    def _authenticate(self):
        usuario_id = self._tokens.verify(_token_from_request())
        # Carrega do banco a cada request: usuário removido/alterado reflete na hora.
        usuario = self._usuarios.get(usuario_id)
        if not usuario:
            raise UnauthorizedError("Sessão inválida: usuário não encontrado")
        g.current_user = usuario
        return usuario

    def login_required(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            self._authenticate()
            return view(*args, **kwargs)

        return wrapper

    def admin_required(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = self._authenticate()
            if usuario.get("tipo") != ADMIN_TIPO:
                raise ForbiddenError("Acesso restrito a administradores")
            return view(*args, **kwargs)

        return wrapper
