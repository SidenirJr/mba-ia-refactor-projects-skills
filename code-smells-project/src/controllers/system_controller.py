"""Endpoints de sistema: index e health (sem vazar segredos/config sensível)."""
from flask import jsonify


class SystemController:
    def __init__(self, service):
        self.service = service

    def index(self):
        return jsonify(self.service.index())

    def health(self):
        return jsonify(self.service.health()), 200
