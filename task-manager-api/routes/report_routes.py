"""Roteamento de relatórios (View)."""
from flask import Blueprint

from controllers import report_controller
from middlewares.auth import login_required

report_bp = Blueprint('reports', __name__)

# Relatórios expõem dados agregados/pessoais — exigem sessão válida (Playbook P13).
report_bp.add_url_rule('/reports/summary', 'summary_report', login_required(report_controller.summary), methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', login_required(report_controller.user_report), methods=['GET'])
