"""Efeitos colaterais de notificação, isolados do controller (antes eram prints na rota)."""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Pedido %s criado para usuário %s — disparando notificações", pedido_id, usuario_id)

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            logger.info("Pedido %s aprovado — preparar envio", pedido_id)
        elif status == "cancelado":
            logger.info("Pedido %s cancelado — devolver estoque", pedido_id)
