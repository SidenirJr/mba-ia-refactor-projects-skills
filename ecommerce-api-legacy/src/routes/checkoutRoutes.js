const express = require('express');

module.exports = (controller) => {
  const router = express.Router();
  router.post('/checkout', controller.checkout);
  return router;
};
