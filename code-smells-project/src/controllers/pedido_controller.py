"""Controller fino de pedidos."""
from flask import jsonify, request


class PedidoController:
    def __init__(self, service):
        self.service = service

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        resultado = self.service.criar(dados.get("usuario_id"), dados.get("itens", []))
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": self.service.listar_por_usuario(usuario_id), "sucesso": True}), 200

    def listar_todos(self):
        return jsonify({"dados": self.service.listar_todos(), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        dados = request.get_json(silent=True) or {}
        self.service.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
