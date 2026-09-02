// Tratamento de erros centralizado — resposta JSON padronizada, sem vazar stack.
// Erros de domínio (4xx) mantêm sua mensagem; erros 5xx respondem mensagem genérica e
// o detalhe real (ex.: "SQLITE_ERROR: ...") fica só no log do servidor.
const GENERIC_SERVER_ERROR = 'Erro interno no servidor';

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  if (status >= 500) {
    console.error(`[ERROR] ${req.method} ${req.originalUrl}`, err);
    return res.status(status).json({ erro: GENERIC_SERVER_ERROR });
  }
  return res.status(status).json({ erro: err.message || GENERIC_SERVER_ERROR });
}

module.exports = { errorHandler };
