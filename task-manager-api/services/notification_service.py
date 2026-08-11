"""Serviço de notificação por e-mail. Credenciais agora vêm da config (antes hardcoded)."""
import logging

import smtplib

from config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.user or not self.password:
            logger.info("SMTP não configurado; e-mail para %s ignorado", to)
            return False
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, to, f"Subject: {subject}\n\n{body}")
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception as exc:
            logger.error("Erro ao enviar email: %s", exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)
