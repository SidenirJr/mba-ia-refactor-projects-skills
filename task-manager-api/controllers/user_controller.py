"""Controller fino de usuários e login: HTTP ↔ UserService.

O controller é a única camada que conhece `flask.g`: ele extrai o usuário
autenticado e repassa ao service, que decide o que esse usuário pode fazer.
"""
from flask import jsonify, request

from middlewares.auth import current_user
from services.user_service import UserService

service = UserService()


def list_users():
    return jsonify(service.list_all(current_user())), 200


def get_user(user_id):
    return jsonify(service.get(user_id, current_user())), 200


def create_user():
    # Rota pública: não há usuário autenticado para repassar.
    return jsonify(service.create(request.get_json(silent=True))), 201


def update_user(user_id):
    return jsonify(service.update(user_id, request.get_json(silent=True), current_user())), 200


def delete_user(user_id):
    service.delete(user_id, current_user())
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify(service.get_tasks(user_id, current_user())), 200


def login():
    data = request.get_json(silent=True) or {}
    return jsonify(service.login(data.get('email'), data.get('password'))), 200
