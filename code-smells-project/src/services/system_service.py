"""Regras dos endpoints de sistema (index/health) — o controller não fala mais SQL."""

VERSAO = "1.0.0"

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SystemService:
    def __init__(self, repo):
        self.repo = repo

    def index(self):
        return {"mensagem": "Bem-vindo à API da Loja", "versao": VERSAO, "endpoints": ENDPOINTS}

    def health(self):
        self.repo.ping()
        return {
            "status": "ok",
            "database": "connected",
            "counts": self.repo.counts(),
            "versao": VERSAO,
        }
