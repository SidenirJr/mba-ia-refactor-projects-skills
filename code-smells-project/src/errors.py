"""Exceções de domínio mapeadas para respostas HTTP pelo error handler central."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message="Erro interno", status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    """Falta de autenticação (sem token / token inválido)."""

    status_code = 401


class ForbiddenError(AppError):
    """Autenticado, mas sem permissão para o recurso."""

    status_code = 403


class ConflictError(AppError):
    """Violação de unicidade / estado conflitante (ex.: e-mail já cadastrado)."""

    status_code = 409


class BusinessError(AppError):
    status_code = 400


class ConfigError(RuntimeError):
    """Configuração obrigatória ausente/ inválida — impede a subida da aplicação."""
