const asyncHandler = require('../middlewares/asyncHandler');

module.exports = (reportService) => ({
  financialReport: asyncHandler(async (req, res) => {
    res.json(await reportService.financialReport());
  }),
});
