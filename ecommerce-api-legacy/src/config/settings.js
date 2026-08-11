require('dotenv').config();

// Configuração por ambiente — nenhum segredo hardcoded no código.
module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'sk_test_sandbox',
  adminToken: process.env.ADMIN_TOKEN || 'dev-admin-token-change-me',
};
