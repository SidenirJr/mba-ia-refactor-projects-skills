"""Regras de negócio de tasks (antes espalhadas nas rotas)."""
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import (
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
    parse_date,
    calculate_percentage,
    utcnow,
)


class TaskService:
    def list_all(self):
        tasks = db.session.execute(
            db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
        ).scalars().all()
        return [self._enrich(t) for t in tasks]

    def get(self, task_id):
        task = self._require(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create(self, data):
        data = data or {}
        title = self._validate_title(data.get('title'))
        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        priority = data.get('priority', 3)
        if not Task.is_valid_priority(priority):
            raise ValidationError('Prioridade deve ser entre 1 e 5')

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=self._validate_user(data.get('user_id')),
            category_id=self._validate_category(data.get('category_id')),
        )
        self._apply_due_date(task, data.get('due_date'))
        self._apply_tags(task, data.get('tags'))

        db.session.add(task)
        db.session.commit()
        return task.to_dict()

    def update(self, task_id, data):
        task = self._require(task_id)
        data = data or {}

        if 'title' in data:
            task.title = self._validate_title(data['title'])
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                raise ValidationError('Status inválido')
            task.status = data['status']
        if 'priority' in data:
            if not Task.is_valid_priority(data['priority']):
                raise ValidationError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']
        if 'user_id' in data:
            task.user_id = self._validate_user(data['user_id'])
        if 'category_id' in data:
            task.category_id = self._validate_category(data['category_id'])
        if 'due_date' in data:
            if data['due_date']:
                self._apply_due_date(task, data['due_date'])
            else:
                task.due_date = None
        if 'tags' in data:
            self._apply_tags(task, data['tags'])

        task.updated_at = utcnow()
        db.session.commit()
        return task.to_dict()

    def delete(self, task_id):
        task = self._require(task_id)
        db.session.delete(task)
        db.session.commit()

    def search(self, query=None, status=None, priority=None, user_id=None):
        stmt = db.select(Task)
        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(Task.title.like(like), Task.description.like(like)))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == self._as_int(priority, 'priority'))
        if user_id:
            stmt = stmt.where(Task.user_id == self._as_int(user_id, 'user_id'))
        tasks = db.session.execute(stmt).scalars().all()
        return [t.to_dict() for t in tasks]

    def stats(self):
        total = db.session.scalar(db.select(func.count()).select_from(Task)) or 0
        by_status = dict(
            db.session.execute(db.select(Task.status, func.count()).group_by(Task.status)).all()
        )
        overdue = db.session.scalar(
            db.select(func.count()).select_from(Task).where(
                Task.due_date.is_not(None),
                Task.due_date < utcnow(),
                Task.status.notin_(['done', 'cancelled']),
            )
        ) or 0
        done = by_status.get('done', 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': overdue,
            'completion_rate': calculate_percentage(done, total),
        }

    # ----- helpers internos -----
    def _enrich(self, task):
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        return data

    def _require(self, task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _validate_title(self, title):
        if not title:
            raise ValidationError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        return title

    def _validate_user(self, user_id):
        if user_id and not db.session.get(User, user_id):
            raise NotFoundError('Usuário não encontrado')
        return user_id

    def _validate_category(self, category_id):
        if category_id and not db.session.get(Category, category_id):
            raise NotFoundError('Categoria não encontrada')
        return category_id

    def _apply_due_date(self, task, due_date):
        if due_date:
            parsed = parse_date(due_date)
            if not parsed:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
            task.due_date = parsed

    def _apply_tags(self, task, tags):
        if tags is None:
            return
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    def _as_int(self, value, field):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError(f'Parâmetro {field} inválido')
