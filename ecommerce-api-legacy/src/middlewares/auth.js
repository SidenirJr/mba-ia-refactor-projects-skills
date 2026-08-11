const settings = require('../config/settings');
const { UnauthorizedError } = require('../errors');

// Guard de admin: protege endpoints sensíveis sem removê-los.
function adminGuard(req, res, next) {
  const token = req.header('X-Admin-Token');
  if (!token || token !== settings.adminToken) {
    return next(new UnauthorizedError('Não autorizado'));
  }
  next();
}

module.exports = { adminGuard };
