"""Controller fino de relatórios: HTTP ↔ ReportService."""
from flask import jsonify

from services.report_service import ReportService

service = ReportService()


def summary():
    return jsonify(service.summary()), 200


def user_report(user_id):
    return jsonify(service.user_report(user_id)), 200
