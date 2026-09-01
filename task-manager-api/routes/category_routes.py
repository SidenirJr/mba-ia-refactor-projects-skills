"""Roteamento de categorias (View) — movido para fora de report_routes, paths preservados."""
from flask import Blueprint

from controllers import category_controller
from middlewares.auth import login_required

category_bp = Blueprint('categories', __name__)

# Categorias organizam tasks de usuários logados (Playbook P13).
category_bp.add_url_rule('/categories', 'get_categories', login_required(category_controller.list_categories), methods=['GET'])
category_bp.add_url_rule('/categories', 'create_category', login_required(category_controller.create_category), methods=['POST'])
category_bp.add_url_rule('/categories/<int:cat_id>', 'update_category', login_required(category_controller.update_category), methods=['PUT'])
category_bp.add_url_rule('/categories/<int:cat_id>', 'delete_category', login_required(category_controller.delete_category), methods=['DELETE'])
