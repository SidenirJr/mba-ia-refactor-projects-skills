"""Acesso a dados de pedidos. Criação é transacional; leitura evita N+1 via JOIN."""


class PedidoRepository:
    def __init__(self, get_db):
        self._get_db = get_db

    def create_with_items(self, usuario_id, itens, total):
        """Insere pedido + itens + baixa de estoque atomicamente.

        `itens`: lista de dicts {produto_id, quantidade, preco}.
        """
        db = self._get_db()
        try:
            db.execute("BEGIN")
            cur = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            )
            pedido_id = cur.lastrowid
            for item in itens:
                db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco"]),
                )
                db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
            db.commit()
            return pedido_id
        except Exception:
            db.rollback()
            raise

    def by_user(self, usuario_id):
        return self._fetch("WHERE usuario_id = ?", (usuario_id,))

    def all(self):
        return self._fetch("", ())

    def _fetch(self, where, params):
        db = self._get_db()
        pedido_rows = db.execute(
            f"SELECT id, usuario_id, status, total, criado_em FROM pedidos {where} ORDER BY id",
            params,
        ).fetchall()
        pedidos = {r["id"]: {**dict(r), "itens": []} for r in pedido_rows}
        if pedidos:
            ids = list(pedidos.keys())
            placeholders = ",".join("?" * len(ids))
            item_rows = db.execute(
                f"""
                SELECT ip.pedido_id, ip.produto_id, pr.nome AS produto_nome,
                       ip.quantidade, ip.preco_unitario
                FROM itens_pedido ip
                LEFT JOIN produtos pr ON pr.id = ip.produto_id
                WHERE ip.pedido_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            for it in item_rows:
                pedidos[it["pedido_id"]]["itens"].append({
                    "produto_id": it["produto_id"],
                    "produto_nome": it["produto_nome"] or "Desconhecido",
                    "quantidade": it["quantidade"],
                    "preco_unitario": it["preco_unitario"],
                })
        return list(pedidos.values())

    def update_status(self, pedido_id, status):
        db = self._get_db()
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))
        db.commit()

    def stats(self):
        db = self._get_db()
        total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = db.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos").fetchone()[0]
        rows = db.execute("SELECT status, COUNT(*) AS c FROM pedidos GROUP BY status").fetchall()
        por_status = {r["status"]: r["c"] for r in rows}
        return {"total_pedidos": total_pedidos, "faturamento": faturamento, "por_status": por_status}
