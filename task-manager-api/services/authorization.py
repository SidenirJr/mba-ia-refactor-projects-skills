"""Regras de autorização compartilhadas pelos services.

Autenticar responde *quem* está chamando; autorizar responde *o que* essa pessoa
pode fazer. O guard de autenticação capturava o usuário e nenhuma camada usava
esse valor — logo "estar logado" equivalia a acesso total. Estas funções fecham
essa lacuna.

O usuário atual chega como parâmetro (`actor`), vindo do controller. Os services
continuam sem importar `flask`, então seguem testáveis sem contexto HTTP.
"""
from errors import ForbiddenError


def is_admin(actor):
    return bool(actor is not None and actor.is_admin())


def require_admin(actor, message='Requer privilégio de administrador'):
    if not is_admin(actor):
        raise ForbiddenError(message)


def require_self_or_admin(actor, owner_id, message='Acesso negado a recurso de outro usuário'):
    if actor is None:
        raise ForbiddenError('Requisição sem usuário autenticado')
    if actor.is_admin() or actor.id == owner_id:
        return
    raise ForbiddenError(message)
