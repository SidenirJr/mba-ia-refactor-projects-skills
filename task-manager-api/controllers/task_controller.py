"""Controller fino de tasks: HTTP ↔ TaskService."""
from flask import jsonify, request

from middlewares.auth import current_user
from services.task_service import TaskService

service = TaskService()


def list_tasks():
    return jsonify(service.list_all(current_user())), 200


def get_task(task_id):
    return jsonify(service.get(task_id, current_user())), 200


def create_task():
    return jsonify(service.create(request.get_json(silent=True), current_user())), 201


def update_task(task_id):
    return jsonify(service.update(task_id, request.get_json(silent=True), current_user())), 200


def delete_task(task_id):
    service.delete(task_id, current_user())
    return jsonify({'message': 'Task deletada com sucesso'}), 200


def search_tasks():
    return jsonify(service.search(
        current_user(),
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )), 200


def task_stats():
    return jsonify(service.stats(current_user())), 200
