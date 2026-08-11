"""Endpoints de sistema: index e health (sem vazar segredos/config sensível)."""
from flask import jsonify

VERSAO = "1.0.0"


class SystemController:
    def __init__(self, get_db):
        self._get_db = get_db

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": VERSAO,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        db = self._get_db()
        db.execute("SELECT 1")
        produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": VERSAO,
        }), 200
