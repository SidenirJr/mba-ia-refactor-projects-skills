const asyncHandler = require('../middlewares/asyncHandler');

// Controller fino: traduz o corpo HTTP (campos usr/eml/pwd/c_id/card) para o serviço.
module.exports = (checkoutService) => ({
  checkout: asyncHandler(async (req, res) => {
    const result = await checkoutService.execute({
      name: req.body.usr,
      email: req.body.eml,
      password: req.body.pwd,
      courseId: req.body.c_id,
      card: req.body.card,
    });
    res.status(200).json(result);
  }),
});
