const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (userService) => ({
  remove: asyncHandler(async (req, res) => {
    const result = await userService.delete(req.params.id);
    res.json({ msg: 'Usuário deletado', ...result });
  }),
});
