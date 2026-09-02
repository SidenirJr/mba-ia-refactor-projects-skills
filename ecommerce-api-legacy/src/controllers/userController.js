const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (userService) => ({
  // Sucesso => 200 com { msg, deleted: true }. Usuário inexistente => o service lança
  // NotFoundError e o error handler responde 404 (antes era 200 com deleted:false).
  remove: asyncHandler(async (req, res) => {
    const result = await userService.delete(req.params.id);
    res.json({ msg: 'Usuário deletado', ...result });
  }),
});
