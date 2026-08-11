"""Regras de negócio de produtos."""
from src.errors import NotFoundError, ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_MIN = 2
NOME_MAX = 200


class ProdutoService:
    def __init__(self, repo):
        self.repo = repo

    def listar(self):
        return self.repo.all()

    def buscar(self, produto_id):
        produto = self.repo.get(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def buscar_lista(self, termo, categoria, preco_min, preco_max):
        return self.repo.search(termo, categoria, preco_min, preco_max)

    def criar(self, dados):
        nome, descricao, preco, estoque, categoria = self._validar(dados)
        return self.repo.create(nome, descricao, preco, estoque, categoria)

    def atualizar(self, produto_id, dados):
        if not self.repo.get(produto_id):
            raise NotFoundError("Produto não encontrado")
        nome, descricao, preco, estoque, categoria = self._validar(dados)
        self.repo.update(produto_id, nome, descricao, preco, estoque, categoria)

    def deletar(self, produto_id):
        if not self.repo.get(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.repo.delete(produto_id)

    def _validar(self, dados):
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                raise ValidationError(f"{campo.capitalize()} é obrigatório")
        nome = dados["nome"]
        preco = dados["preco"]
        estoque = dados["estoque"]
        if isinstance(preco, bool) or not isinstance(preco, (int, float)):
            raise ValidationError("Preço deve ser numérico")
        if isinstance(estoque, bool) or not isinstance(estoque, int):
            raise ValidationError("Estoque deve ser um inteiro")
        if preco < 0:
            raise ValidationError("Preço não pode ser negativo")
        if estoque < 0:
            raise ValidationError("Estoque não pode ser negativo")
        if len(nome) < NOME_MIN:
            raise ValidationError("Nome muito curto")
        if len(nome) > NOME_MAX:
            raise ValidationError("Nome muito longo")
        categoria = dados.get("categoria", "geral")
        if categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))
        return nome, dados.get("descricao", ""), preco, estoque, categoria
