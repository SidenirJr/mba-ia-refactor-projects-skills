const express = require('express');

const { adminGuard } = require('../middlewares/auth');

module.exports = (controller) => {
  const router = express.Router();
  router.delete('/users/:id', adminGuard, controller.remove);
  return router;
};
