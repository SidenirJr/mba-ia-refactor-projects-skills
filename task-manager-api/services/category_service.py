"""Regras de negócio de categorias (antes misturadas no report_routes)."""
from sqlalchemy import func

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from utils.helpers import DEFAULT_COLOR


class CategoryService:
    def list_all(self):
        counts = dict(
            db.session.execute(
                db.select(Task.category_id, func.count()).group_by(Task.category_id)
            ).all()
        )
        categories = db.session.execute(db.select(Category)).scalars().all()
        return [{**c.to_dict(), 'task_count': counts.get(c.id, 0)} for c in categories]

    def create(self, data):
        data = data or {}
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')
        category = Category(
            name=name,
            description=data.get('description', ''),
            color=data.get('color', DEFAULT_COLOR),
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update(self, category_id, data):
        category = self._require(category_id)
        data = data or {}
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']
        db.session.commit()
        return category.to_dict()

    def delete(self, category_id):
        category = self._require(category_id)
        # desvincula as tasks (evita category_id órfão) em transação
        db.session.execute(
            db.update(Task).where(Task.category_id == category_id).values(category_id=None)
        )
        db.session.delete(category)
        db.session.commit()

    def _require(self, category_id):
        category = db.session.get(Category, category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category
