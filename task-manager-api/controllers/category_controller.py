"""Controller fino de categorias: HTTP ↔ CategoryService."""
from flask import jsonify, request

from middlewares.auth import current_user
from services.category_service import CategoryService

service = CategoryService()


def list_categories():
    return jsonify(service.list_all(current_user())), 200


def create_category():
    return jsonify(service.create(request.get_json(silent=True), current_user())), 201


def update_category(cat_id):
    return jsonify(service.update(cat_id, request.get_json(silent=True), current_user())), 200


def delete_category(cat_id):
    service.delete(cat_id, current_user())
    return jsonify({'message': 'Categoria deletada'}), 200
