"""Relatórios e agregações — substitui os loops N+1 das rotas por queries agregadas."""
from datetime import timedelta

from sqlalchemy import case, func

from database import db
from errors import NotFoundError
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import calculate_percentage, utcnow


class ReportService:
    def summary(self):
        now = utcnow()
        seven_days_ago = now - timedelta(days=7)

        total_tasks = db.session.scalar(db.select(func.count()).select_from(Task)) or 0
        total_users = db.session.scalar(db.select(func.count()).select_from(User)) or 0
        total_categories = db.session.scalar(db.select(func.count()).select_from(Category)) or 0

        by_status = dict(
            db.session.execute(db.select(Task.status, func.count()).group_by(Task.status)).all()
        )
        by_priority = dict(
            db.session.execute(db.select(Task.priority, func.count()).group_by(Task.priority)).all()
        )

        overdue_tasks = db.session.execute(
            db.select(Task).where(
                Task.due_date.is_not(None),
                Task.due_date < now,
                Task.status.notin_(['done', 'cancelled']),
            )
        ).scalars().all()
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - t.due_date).days,
            }
            for t in overdue_tasks
        ]

        recent_tasks = db.session.scalar(
            db.select(func.count()).select_from(Task).where(Task.created_at >= seven_days_ago)
        ) or 0
        recent_done = db.session.scalar(
            db.select(func.count()).select_from(Task).where(
                Task.status == 'done', Task.updated_at >= seven_days_ago
            )
        ) or 0

        # produtividade por usuário em uma única query agregada (sem N+1)
        done_expr = func.sum(case((Task.status == 'done', 1), else_=0))
        rows = db.session.execute(
            db.select(User.id, User.name, func.count(Task.id), done_expr)
            .select_from(User)
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
        ).all()
        user_stats = [
            {
                'user_id': uid,
                'user_name': name,
                'total_tasks': total or 0,
                'completed_tasks': int(done or 0),
                'completion_rate': calculate_percentage(int(done or 0), total or 0),
            }
            for uid, name, total, done in rows
        ]

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': by_status.get('pending', 0),
                'in_progress': by_status.get('in_progress', 0),
                'done': by_status.get('done', 0),
                'cancelled': by_status.get('cancelled', 0),
            },
            'tasks_by_priority': {
                'critical': by_priority.get(1, 0),
                'high': by_priority.get(2, 0),
                'medium': by_priority.get(3, 0),
                'low': by_priority.get(4, 0),
                'minimal': by_priority.get(5, 0),
            },
            'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = db.session.execute(
            db.select(Task).where(Task.user_id == user_id)
        ).scalars().all()

        total = len(tasks)
        counters = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            if t.status in counters:
                counters[t.status] += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counters['done'],
                'pending': counters['pending'],
                'in_progress': counters['in_progress'],
                'cancelled': counters['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(counters['done'], total),
            },
        }
