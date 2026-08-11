const express = require('express');

const { adminGuard } = require('../middlewares/auth');

module.exports = (controller) => {
  const router = express.Router();
  router.get('/admin/financial-report', adminGuard, controller.financialReport);
  return router;
};
