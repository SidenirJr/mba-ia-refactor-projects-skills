"""Controller fino de produtos: traduz HTTP ↔ serviço."""
from flask import jsonify, request


class ProdutoController:
    def __init__(self, service):
        self.service = service

    def listar(self):
        return jsonify({"dados": self.service.listar(), "sucesso": True}), 200

    def buscar(self, produto_id):
        return jsonify({"dados": self.service.buscar(produto_id), "sucesso": True}), 200

    def buscar_lista(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria") or None
        preco_min = request.args.get("preco_min")
        preco_max = request.args.get("preco_max")
        preco_min = float(preco_min) if preco_min not in (None, "") else None
        preco_max = float(preco_max) if preco_max not in (None, "") else None
        resultados = self.service.buscar_lista(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        novo_id = self.service.criar(dados)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        dados = request.get_json(silent=True)
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        self.service.atualizar(produto_id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self.service.deletar(produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
