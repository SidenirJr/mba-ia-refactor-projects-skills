"""Regras de negócio dos endpoints administrativos.

`/admin/query` deixou de executar SQL arbitrário: aceita **uma única instrução SELECT**
sobre uma allowlist de tabelas do domínio. Tudo o mais (múltiplas instruções, comentários
SQL, palavras-chave de escrita/DDL, PRAGMA/ATTACH, coluna `senha`) é recusado com 400.
A execução ainda passa por um authorizer somente-leitura no repository (defesa em camadas).
"""
import re

from src.errors import ValidationError

TABELAS_PERMITIDAS = ("produtos", "usuarios", "pedidos", "itens_pedido")
COLUNAS_PROIBIDAS = ("senha",)

# Palavras-chave de escrita/DDL/administração do banco — nenhuma é aceita.
PALAVRAS_PROIBIDAS = (
    "insert", "update", "delete", "drop", "alter", "create", "replace", "truncate",
    "attach", "detach", "pragma", "vacuum", "reindex", "analyze", "trigger", "grant",
    "revoke", "begin", "commit", "rollback", "savepoint", "release", "into", "exec",
    "execute", "load_extension", "returning",
)

_COMENTARIOS = ("--", "/*", "*/")
_RE_TABELAS = re.compile(r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_RE_FROM_JOIN = re.compile(r"\b(?:from|join)\b", re.IGNORECASE)


class AdminService:
    def __init__(self, repo, tabelas_permitidas=TABELAS_PERMITIDAS):
        self.repo = repo
        self.tabelas_permitidas = tuple(t.lower() for t in tabelas_permitidas)

    def reset_db(self):
        self.repo.reset()
        return {"mensagem": "Banco de dados resetado"}

    def executar_consulta(self, sql):
        sql_validado = self._validar_select(sql)
        rows = self.repo.run_readonly_select(sql_validado, self.tabelas_permitidas)
        # Rede de segurança: a coluna `senha` nunca sai por este endpoint (ex.: SELECT *).
        return [
            {k: v for k, v in row.items() if k.lower() not in COLUNAS_PROIBIDAS}
            for row in rows
        ]

    def _validar_select(self, sql):
        if not isinstance(sql, str) or not sql.strip():
            raise ValidationError("Query não informada")

        sql = sql.strip()
        for marcador in _COMENTARIOS:
            if marcador in sql:
                raise ValidationError(
                    "Comentários SQL não são permitidos neste endpoint"
                )

        # Uma única instrução: tolera apenas o `;` final.
        sem_ponto_e_virgula = sql.rstrip().rstrip(";").rstrip()
        if ";" in sem_ponto_e_virgula:
            raise ValidationError(
                "Apenas uma instrução por requisição — múltiplas instruções são recusadas"
            )
        sql = sem_ponto_e_virgula
        if not sql:
            raise ValidationError("Query não informada")

        minusculo = sql.lower()
        if not re.match(r"^select\b", minusculo):
            raise ValidationError(
                "Apenas consultas SELECT são permitidas neste endpoint"
            )

        for palavra in PALAVRAS_PROIBIDAS:
            if re.search(r"\b%s\b" % re.escape(palavra), minusculo):
                raise ValidationError(
                    f"Palavra-chave não permitida em consultas administrativas: {palavra.upper()}"
                )

        for coluna in COLUNAS_PROIBIDAS:
            if re.search(r"\b%s\b" % re.escape(coluna), minusculo):
                raise ValidationError(
                    f"A coluna `{coluna}` não pode ser consultada por este endpoint"
                )

        tabelas = [t.lower() for t in _RE_TABELAS.findall(sql)]
        # Toda cláusula FROM/JOIN precisa referenciar uma tabela nomeada e permitida
        # (subqueries e funções table-valued como pragma_* caem aqui).
        if not tabelas or len(tabelas) != len(_RE_FROM_JOIN.findall(sql)):
            raise ValidationError(
                "A consulta deve referenciar diretamente as tabelas permitidas: "
                + ", ".join(self.tabelas_permitidas)
            )
        for tabela in tabelas:
            if tabela not in self.tabelas_permitidas:
                raise ValidationError(
                    f"Tabela não permitida: {tabela}. Permitidas: "
                    + ", ".join(self.tabelas_permitidas)
                )
        return sql
