require('dotenv').config();

// Configuração 100% por ambiente. Os segredos (ADMIN_TOKEN, PAYMENT_GATEWAY_KEY) NÃO têm
// default: sem eles a aplicação falha na inicialização em vez de subir com um valor
// versionado (e portanto público) que qualquer leitor do repositório conheceria.
const REQUIRED_SECRETS = ['ADMIN_TOKEN', 'PAYMENT_GATEWAY_KEY'];

function requireSecrets() {
  const missing = REQUIRED_SECRETS.filter((name) => !String(process.env[name] || '').trim());
  if (missing.length > 0) {
    throw new Error(
      `Configuração obrigatória ausente: ${missing.join(', ')}. `
      + 'Defina essas variáveis de ambiente (ou no .env, veja .env.example) antes de iniciar a aplicação. '
      + 'Não existe valor default para segredos.',
    );
  }
}

requireSecrets();

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  adminToken: process.env.ADMIN_TOKEN,
};
