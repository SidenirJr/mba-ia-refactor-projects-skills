"""Roteamento de usuários e login (View)."""
from flask import Blueprint

from controllers import user_controller
from middlewares.auth import admin_required, login_required

user_bp = Blueprint('users', __name__)

# Cadastro e login ficam públicos — são o meio de OBTER o token (Playbook P13).
user_bp.add_url_rule('/users', 'create_user', user_controller.create_user, methods=['POST'])
user_bp.add_url_rule('/login', 'login', user_controller.login, methods=['POST'])

# Demais rotas operam sobre dados de usuário e exigem sessão válida.
# A listagem completa de usuários é dado de administração (Playbook P12).
user_bp.add_url_rule('/users', 'get_users', admin_required(user_controller.list_users), methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', 'get_user', login_required(user_controller.get_user), methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', 'update_user', login_required(user_controller.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', 'delete_user', login_required(user_controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks', login_required(user_controller.get_user_tasks), methods=['GET'])
