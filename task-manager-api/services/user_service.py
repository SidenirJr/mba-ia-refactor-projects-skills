"""Regras de negócio de usuários, autenticação (token assinado) e dependências."""
from sqlalchemy import func

from database import db
from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from middlewares.auth import _serializer
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, is_valid_email


class UserService:
    def list_all(self):
        counts = dict(
            db.session.execute(
                db.select(Task.user_id, func.count()).group_by(Task.user_id)
            ).all()
        )
        users = db.session.execute(db.select(User)).scalars().all()
        return [{**u.to_dict(), 'task_count': counts.get(u.id, 0)} for u in users]

    def get(self, user_id):
        user = self._require(user_id)
        data = user.to_dict()
        tasks = db.session.execute(
            db.select(Task).where(Task.user_id == user_id)
        ).scalars().all()
        data['tasks'] = [t.to_dict() for t in tasks]
        return data

    def get_tasks(self, user_id):
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
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name or not email or not password:
            raise ValidationError('Nome, email e senha são obrigatórios')
        if not is_valid_email(email):
            raise ValidationError('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')
        if self._find_by_email(email):
            raise ConflictError('Email já cadastrado')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    def update(self, user_id, data):
        user = self._require(user_id)
        data = data or {}

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError('Email inválido')
            existing = self._find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    def delete(self, user_id):
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
        token = _serializer().dumps({'user_id': user.id})
        return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}

    # ----- helpers internos -----
    def _require(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def _find_by_email(self, email):
        return db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one_or_none()
