"""Acesso a dados de usuários. A coluna `senha` (hash) nunca sai em consultas públicas;
só é lida no fluxo de autenticação."""
import sqlite3

from src.errors import ConflictError


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

    def find_by_email(self, email):
        """Consulta pública por e-mail (sem hash) — usada na checagem de duplicidade."""
        row = self._get_db().execute(
            f"SELECT {self.PUBLIC_COLUMNS} FROM usuarios WHERE email = ?", (email,)
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
        try:
            cur = db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        except sqlite3.IntegrityError:
            # UNIQUE(email) — cobre a corrida entre a checagem do service e o INSERT.
            db.rollback()
            raise ConflictError("Email já cadastrado")
        db.commit()
        return cur.lastrowid
