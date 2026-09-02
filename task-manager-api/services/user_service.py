"""Regras de negócio de usuários, autenticação (token assinado) e dependências."""
from sqlalchemy import func

from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import User
from services.authorization import is_admin, require_admin, require_self_or_admin
from services.token_service import TokenService
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, is_valid_email


class UserService:
    def __init__(self, token_service=None):
        self.token_service = token_service or TokenService()

    def list_all(self, actor):
        # A listagem devolve o e-mail de todos os cadastrados: é dado de administração.
        require_admin(actor)
        counts = dict(
            db.session.execute(
                db.select(Task.user_id, func.count()).group_by(Task.user_id)
            ).all()
        )
        users = db.session.execute(db.select(User)).scalars().all()
        return [{**u.to_dict(), 'task_count': counts.get(u.id, 0)} for u in users]

    def get(self, user_id, actor):
        require_self_or_admin(actor, user_id)
        user = self._require(user_id)
        data = user.to_dict()
        tasks = db.session.execute(
            db.select(Task).where(Task.user_id == user_id)
        ).scalars().all()
        data['tasks'] = [t.to_dict() for t in tasks]
        return data

    def get_tasks(self, user_id, actor):
        require_self_or_admin(actor, user_id)
        self._require(user_id)
        tasks = db.session.execute(
            db.select(Task).where(Task.user_id == user_id)
        ).scalars().all()
        result = []
        for t in tasks:
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            result.append(data)
        return result

    def create(self, data):
        data = data or {}
        name = self._validate_name(data.get('name'))
        email = data.get('email')
        password = self._validate_password(data.get('password'))

        if not email:
            raise ValidationError('Nome, email e senha são obrigatórios')
        if not is_valid_email(email):
            raise ValidationError('Email inválido')
        if self._find_by_email(email):
            raise ConflictError('Email já cadastrado')

        # `role` é campo de privilégio e não é atribuível pelo cliente: o cadastro
        # é uma rota pública, então um `role` no corpo é IGNORADO e todo usuário
        # nasce como 'user'. Sem isso, qualquer anônimo se registraria como admin
        # (mass assignment). Promover alguém é ação de admin, via PUT /users/<id>.
        role = 'user'

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    def update(self, user_id, data, actor):
        require_self_or_admin(actor, user_id)
        user = self._require(user_id)
        data = data or {}

        if 'name' in data:
            user.name = self._validate_name(data['name'])
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError('Email inválido')
            existing = self._find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            new_password = self._validate_password(data['password'])
            # Trocar a própria senha exige provar a senha atual; sem isso, uma
            # sessão vazada viraria takeover permanente da conta.
            if not is_admin(actor):
                current = data.get('current_password')
                if not current or not user.check_password(current):
                    raise ForbiddenError('Senha atual obrigatória para alterar a senha')
            user.set_password(new_password)
        if 'role' in data:
            require_admin(actor, 'Apenas um administrador pode alterar o role de um usuário')
            user.role = self._validate_role(data['role'])
        if 'active' in data:
            require_admin(actor, 'Apenas um administrador pode ativar ou desativar um usuário')
            if not isinstance(data['active'], bool):
                raise ValidationError('Campo active deve ser booleano')
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    def delete(self, user_id, actor):
        require_self_or_admin(actor, user_id)
        user = self._require(user_id)
        # remove as tasks do usuário em transação (evita FK órfã)
        db.session.execute(db.delete(Task).where(Task.user_id == user_id))
        db.session.delete(user)
        db.session.commit()

    def login(self, email, password):
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        user = self._find_by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        token = self.token_service.generate(user.id)
        return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}

    # ----- helpers internos -----
    def _require(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def _find_by_email(self, email):
        if not isinstance(email, str):
            return None
        return db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()

    def _validate_name(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValidationError('Nome é obrigatório')
        return name

    def _validate_password(self, password):
        if not isinstance(password, str) or not password:
            raise ValidationError('Senha é obrigatória')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        return password

    def _validate_role(self, role):
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')
        return role
