"""Regras de negócio de usuários e autenticação (hash de senha + token de sessão)."""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from src.services.authorization import require_self_or_admin

EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


class UsuarioService:
    def __init__(self, repo, auth_token_service=None):
        self.repo = repo
        self.tokens = auth_token_service

    def listar(self):
        return self.repo.all()

    def buscar(self, usuario_id, current_user=None):
        # Autorização de dono/papel: recebida por parâmetro (o controller resolve o
        # usuário atual). O service não conhece Flask.
        require_self_or_admin(current_user, usuario_id)
        usuario = self.repo.get(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        if not EMAIL_RE.match(email):
            raise ValidationError("Email inválido")
        if self.repo.find_by_email(email):
            raise ConflictError("Email já cadastrado")
        senha_hash = generate_password_hash(senha, method="pbkdf2:sha256")
        # O repository também converte violação de UNIQUE em ConflictError (corrida).
        return self.repo.create(nome, email, senha_hash)

    def login(self, email, senha):
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        usuario = self.repo.get_credentials_by_email(email)
        if not usuario or not check_password_hash(usuario["senha"], senha):
            raise UnauthorizedError("Email ou senha inválidos")
        dados = {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        }
        if self.tokens:
            dados["token"] = self.tokens.issue(usuario["id"])
        return dados
