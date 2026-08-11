// Tratamento de erros centralizado — resposta JSON padronizada, sem vazar stack.
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  const status = err.statusCode || 500;
  if (status >= 500) {
    console.error('[ERROR]', err.message);
  }
  res.status(status).json({ erro: err.message || 'Erro interno' });
}

module.exports = { errorHandler };
