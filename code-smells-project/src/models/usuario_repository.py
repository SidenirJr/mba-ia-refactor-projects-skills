"""Acesso a dados de usuários. A coluna `senha` (hash) nunca sai em consultas públicas;
só é lida no fluxo de autenticação."""


class UsuarioRepository:
    PUBLIC_COLUMNS = "id, nome, email, tipo, criado_em"  # sem `senha`

    def __init__(self, get_db):
        self._get_db = get_db

    def all(self):
        rows = self._get_db().execute(
            f"SELECT {self.PUBLIC_COLUMNS} FROM usuarios"
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, usuario_id):
        row = self._get_db().execute(
            f"SELECT {self.PUBLIC_COLUMNS} FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_credentials_by_email(self, email):
        """Inclui o hash da senha — uso restrito à autenticação."""
        row = self._get_db().execute(
            "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return dict(row) if row else None

    def create(self, nome, email, senha_hash, tipo="cliente"):
        db = self._get_db()
        cur = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        db.commit()
        return cur.lastrowid
