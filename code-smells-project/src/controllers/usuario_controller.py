"""Controller fino de usuários e login."""
from flask import g, jsonify, request


class UsuarioController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def buscar(self, usuario_id):
        # O controller resolve o usuário atual (flask.g) e o passa ao service, que aplica
        # a regra de dono/admin — o service continua sem conhecer Flask.
        dados = self.service.buscar(usuario_id, g.get("current_user"))
        return jsonify({"dados": dados, "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        novo_id = self.service.criar(dados)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json(silent=True) or {}
        usuario = self.service.login(dados.get("email", ""), dados.get("senha", ""))
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
