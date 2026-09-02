"""Acesso a dados dos endpoints administrativos.

Todo o SQL dos endpoints `/admin/*` mora aqui (antes estava no controller). A execução
de consultas ad-hoc é somente leitura e reforçada por um *authorizer* do SQLite: mesmo
que a validação sintática do service falhasse, o motor recusa qualquer operação que não
seja leitura das tabelas permitidas.
"""
import sqlite3

from src.errors import ValidationError

TABELAS_DOMINIO = ("itens_pedido", "pedidos", "produtos", "usuarios")
COLUNAS_NEGADAS = ("senha",)  # nunca lidas por consultas administrativas


class AdminRepository:
    def __init__(self, get_db):
        self._get_db = get_db

    def reset(self, tabelas=TABELAS_DOMINIO):
        db = self._get_db()
        for tabela in tabelas:  # lista fixa — sem interpolação de input
            db.execute(f"DELETE FROM {tabela}")
        db.commit()

    def run_readonly_select(self, sql, tabelas_permitidas):
        """Executa um SELECT já validado, com authorizer somente-leitura."""
        db = self._get_db()
        permitidas = {t.lower() for t in tabelas_permitidas}
        self._set_authorizer(db, permitidas)
        try:
            rows = db.execute(sql).fetchall()
        except sqlite3.DatabaseError:
            # O authorizer recusou algo que passou pela validação sintática.
            raise ValidationError(
                "Consulta recusada: apenas leitura das tabelas "
                + ", ".join(sorted(permitidas))
                + " é permitida"
            )
        finally:
            self._set_authorizer(db, None)
        return [dict(r) for r in rows]

    @staticmethod
    def _set_authorizer(db, permitidas):
        if permitidas is None:
            db.set_authorizer(None)
            return

        def authorizer(action, arg1, arg2, db_name, trigger):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ:
                tabela = (arg1 or "").lower()
                coluna = (arg2 or "").lower()
                if tabela not in permitidas:
                    return sqlite3.SQLITE_DENY
                if coluna in COLUNAS_NEGADAS:
                    # IGNORE devolve NULL na coluna (ex.: `SELECT *`) em vez de quebrar;
                    # a chave ainda é removida do payload pelo service.
                    return sqlite3.SQLITE_IGNORE
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION:
                # Funções escalares/agregadas são permitidas, exceto carga de extensões.
                if (arg2 or "").lower() in ("load_extension", "readfile", "writefile"):
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        db.set_authorizer(authorizer)
