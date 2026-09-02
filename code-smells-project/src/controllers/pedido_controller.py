"""Controller fino de pedidos."""
from flask import g, jsonify, request


class PedidoController:
    def __init__(self, service):
        self.service = service

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        # `usuario_id` do corpo é deliberadamente ignorado: o dono do pedido é o usuário
        # autenticado (o service deriva do token).
        resultado = self.service.criar(g.get("current_user"), dados.get("itens", []))
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_por_usuario(self, usuario_id):
        dados = self.service.listar_por_usuario(usuario_id, g.get("current_user"))
        return jsonify({"dados": dados, "sucesso": True}), 200

    def listar_todos(self):
        return jsonify({"dados": self.service.listar_todos(), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        dados = request.get_json(silent=True) or {}
        self.service.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
