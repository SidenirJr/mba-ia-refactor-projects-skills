"""Acesso a dados de produtos — todas as queries são parametrizadas (sem SQL injection)."""


class ProdutoRepository:
    COLUMNS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"

    def __init__(self, get_db):
        self._get_db = get_db

    def all(self):
        rows = self._get_db().execute(f"SELECT {self.COLUMNS} FROM produtos").fetchall()
        return [dict(r) for r in rows]

    def get(self, produto_id):
        row = self._get_db().execute(
            f"SELECT {self.COLUMNS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def create(self, nome, descricao, preco, estoque, categoria):
        db = self._get_db()
        cur = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cur.lastrowid

    def update(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._get_db()
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        db.commit()

    def delete(self, produto_id):
        db = self._get_db()
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()

    def search(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        sql = f"SELECT {self.COLUMNS} FROM produtos WHERE 1 = 1"
        params = []
        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:  # corrige o bug de falsy (preco_min=0)
            sql += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            sql += " AND preco <= ?"
            params.append(preco_max)
        rows = self._get_db().execute(sql, params).fetchall()
        return [dict(r) for r in rows]
