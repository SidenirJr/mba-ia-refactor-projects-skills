"""Endpoints administrativos. Continuam existindo, mas agora protegidos por admin-guard
(ver registro de rotas). A execução de SQL arbitrário permanece sensível por natureza —
mantida sob autenticação conforme decisão de preservar os endpoints."""
from flask import jsonify, request

TABELAS = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdminController:
    def __init__(self, get_db):
        self._get_db = get_db

    def reset_db(self):
        db = self._get_db()
        for tabela in TABELAS:  # lista fixa — sem interpolação de input
            db.execute(f"DELETE FROM {tabela}")
        db.commit()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    def query(self):
        dados = request.get_json(silent=True) or {}
        sql = dados.get("sql", "")
        if not sql:
            return jsonify({"erro": "Query não informada"}), 400
        db = self._get_db()
        cur = db.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            rows = cur.fetchall()
            return jsonify({"dados": [dict(r) for r in rows], "sucesso": True}), 200
        db.commit()
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
