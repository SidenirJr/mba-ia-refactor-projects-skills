"""Regras de negócio de categorias (antes misturadas no report_routes)."""
from sqlalchemy import func

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from services.authorization import require_admin
from utils.helpers import DEFAULT_COLOR


class CategoryService:
    def list_all(self, actor=None):
        counts = dict(
            db.session.execute(
                db.select(Task.category_id, func.count()).group_by(Task.category_id)
            ).all()
        )
        categories = db.session.execute(db.select(Category)).scalars().all()
        return [{**c.to_dict(), 'task_count': counts.get(c.id, 0)} for c in categories]

    def create(self, data, actor):
        # Categoria é taxonomia compartilhada por todos os usuários: escrever nela
        # afeta as tasks de terceiros, então é ação de administração.
        require_admin(actor, 'Apenas um administrador pode criar categorias')
        data = data or {}
        category = Category(
            name=self._validate_name(data.get('name')),
            description=self._validate_text(data.get('description', ''), 'description'),
            color=self._validate_text(data.get('color', DEFAULT_COLOR), 'color'),
        )
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update(self, category_id, data, actor):
        require_admin(actor, 'Apenas um administrador pode alterar categorias')
        category = self._require(category_id)
        data = data or {}
        if 'name' in data:
            category.name = self._validate_name(data['name'])
        if 'description' in data:
            category.description = self._validate_text(data['description'], 'description')
        if 'color' in data:
            category.color = self._validate_text(data['color'], 'color')
        db.session.commit()
        return category.to_dict()

    def delete(self, category_id, actor):
        require_admin(actor, 'Apenas um administrador pode remover categorias')
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

    def _validate_name(self, name):
        # Sem esta checagem, `{"name": null}` chegava ao banco e estourava a
        # constraint NOT NULL como 500 em vez de 400.
        if not isinstance(name, str) or not name.strip():
            raise ValidationError('Nome é obrigatório')
        return name

    def _validate_text(self, value, field):
        if value is None:
            return ''
        if not isinstance(value, str):
            raise ValidationError(f'Campo {field} deve ser texto')
        return value
