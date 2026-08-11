// Erros de domínio mapeados para status HTTP pelo error handler central.

class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Requisição inválida') { super(message, 400); }
}

class NotFoundError extends AppError {
  constructor(message = 'Não encontrado') { super(message, 404); }
}

class PaymentError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 400); }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Não autorizado') { super(message, 401); }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentError, UnauthorizedError };
