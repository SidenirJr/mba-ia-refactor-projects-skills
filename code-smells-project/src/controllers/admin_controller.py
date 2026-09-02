"""Endpoints administrativos (HTTP fino).

Protegidos por header `X-Admin-Token` **e** sessão de usuário admin (ver routes.py).
Nenhum SQL aqui: o controller delega para o `AdminService`, que valida a consulta, e o
`AdminRepository`, que a executa em modo somente-leitura.
"""
from flask import jsonify, request


class AdminController:
    def __init__(self, service):
        self.service = service

    def reset_db(self):
        resultado = self.service.reset_db()
        return jsonify({"mensagem": resultado["mensagem"], "sucesso": True}), 200

    def query(self):
        dados = request.get_json(silent=True) or {}
        linhas = self.service.executar_consulta(dados.get("sql", ""))
        return jsonify({"dados": linhas, "sucesso": True}), 200
