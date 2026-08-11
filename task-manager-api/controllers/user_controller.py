"""Controller fino de usuários e login: HTTP ↔ UserService."""
from flask import jsonify, request

from services.user_service import UserService

service = UserService()


def list_users():
    return jsonify(service.list_all()), 200


def get_user(user_id):
    return jsonify(service.get(user_id)), 200


def create_user():
    return jsonify(service.create(request.get_json(silent=True))), 201


def update_user(user_id):
    return jsonify(service.update(user_id, request.get_json(silent=True))), 200


def delete_user(user_id):
    service.delete(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


def get_user_tasks(user_id):
    return jsonify(service.get_tasks(user_id)), 200


def login():
    data = request.get_json(silent=True) or {}
    return jsonify(service.login(data.get('email'), data.get('password'))), 200
