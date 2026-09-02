"""Regras de autorização de domínio (dono do recurso / papel).

Vive na camada de serviço e recebe o usuário atual como parâmetro — nenhum service
importa Flask nem lê `flask.g`. Quem resolve o usuário atual é o controller.
"""
from src.errors import ForbiddenError, UnauthorizedError

ADMIN_TIPO = "admin"


def is_admin(current_user):
    return bool(current_user) and current_user.get("tipo") == ADMIN_TIPO


def require_user(current_user):
    if not current_user or not current_user.get("id"):
        raise UnauthorizedError("Autenticação obrigatória")
    return current_user


def require_self_or_admin(current_user, usuario_id):
    """Permite acesso ao próprio recurso; admin acessa qualquer um."""
    require_user(current_user)
    if is_admin(current_user):
        return
    if int(current_user["id"]) != int(usuario_id):
        raise ForbiddenError("Acesso permitido apenas ao próprio usuário")
