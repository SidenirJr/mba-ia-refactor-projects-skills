"""Acesso a dados dos endpoints de sistema (health) — antes o SQL vivia no controller."""


class SystemRepository:
    def __init__(self, get_db):
        self._get_db = get_db

    def ping(self):
        self._get_db().execute("SELECT 1")
        return True

    def counts(self):
        db = self._get_db()
        return {
            "produtos": db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
            "usuarios": db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
            "pedidos": db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
        }
