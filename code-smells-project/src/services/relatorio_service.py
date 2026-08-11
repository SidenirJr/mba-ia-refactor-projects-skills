"""Regras de negócio do relatório de vendas (faixas de desconto antes embutidas no model)."""


class RelatorioService:
    # (limite de faturamento, taxa de desconto) — antes eram magic numbers soltos
    DESCONTO_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

    def __init__(self, pedido_repo):
        self.repo = pedido_repo

    def _desconto(self, faturamento):
        for limite, taxa in self.DESCONTO_TIERS:
            if faturamento > limite:
                return faturamento * taxa
        return 0

    def vendas(self):
        stats = self.repo.stats()
        faturamento = stats["faturamento"]
        total_pedidos = stats["total_pedidos"]
        por_status = stats["por_status"]
        desconto = self._desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": por_status.get("pendente", 0),
            "pedidos_aprovados": por_status.get("aprovado", 0),
            "pedidos_cancelados": por_status.get("cancelado", 0),
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }
