// Encaminha erros de handlers async para o error handler central (Express 4 não faz isso sozinho).
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
