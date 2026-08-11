"""Regras de negócio de pedidos: validação, cálculo de total, estoque e orquestração."""
from src.errors import BusinessError, NotFoundError, ValidationError

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class PedidoService:
    def __init__(self, pedido_repo, produto_repo, notification_service=None):
        self.pedido_repo = pedido_repo
        self.produto_repo = produto_repo
        self.notifications = notification_service

    def criar(self, usuario_id, itens):
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        resolved = []
        total = 0
        for item in itens:
            if "produto_id" not in item or "quantidade" not in item:
                raise ValidationError("Item inválido: produto_id e quantidade são obrigatórios")
            produto = self.produto_repo.get(item["produto_id"])
            if not produto:
                raise NotFoundError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise BusinessError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
            resolved.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco": produto["preco"],
            })

        pedido_id = self.pedido_repo.create_with_items(usuario_id, resolved, total)
        if self.notifications:
            self.notifications.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_por_usuario(self, usuario_id):
        return self.pedido_repo.by_user(usuario_id)

    def listar_todos(self):
        return self.pedido_repo.all()

    def atualizar_status(self, pedido_id, status):
        if status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        self.pedido_repo.update_status(pedido_id, status)
        if self.notifications:
            self.notifications.status_alterado(pedido_id, status)
