const express = require('express');

// Fail-fast de configuração: settings.js lança se ADMIN_TOKEN/PAYMENT_GATEWAY_KEY não
// vierem do ambiente. Sem isso a app subiria com segredos default versionados.
try {
  require('./config/settings');
} catch (err) {
  console.error(`[config] ${err.message}`);
  if (require.main === module) process.exit(1);
  throw err;
}

const settings = require('./config/settings');
const { Database, initSchema } = require('./config/database');

const UserRepository = require('./models/userRepository');
const CourseRepository = require('./models/courseRepository');
const EnrollmentRepository = require('./models/enrollmentRepository');
const PaymentRepository = require('./models/paymentRepository');
const AuditLogRepository = require('./models/auditLogRepository');
const ReportRepository = require('./models/reportRepository');

const passwordHasher = require('./services/passwordHasher');
const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');

const checkoutController = require('./controllers/checkoutController');
const reportController = require('./controllers/reportController');
const userController = require('./controllers/userController');

const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const { errorHandler } = require('./middlewares/errorHandler');
const { NotFoundError } = require('./errors');

// Composition root: cria o banco, instancia e injeta as dependências, monta as rotas.
async function createApp() {
  const db = new Database(settings.dbPath);
  await initSchema(db);

  // Repositories
  const userRepository = new UserRepository(db);
  const courseRepository = new CourseRepository(db);
  const enrollmentRepository = new EnrollmentRepository(db);
  const paymentRepository = new PaymentRepository(db);
  const auditLogRepository = new AuditLogRepository(db);
  const reportRepository = new ReportRepository(db);

  // Services
  const paymentGateway = new PaymentGateway(settings.paymentGatewayKey);
  const checkoutService = new CheckoutService({
    db,
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    paymentGateway,
    passwordHasher,
  });
  const reportService = new ReportService(reportRepository);
  const userService = new UserService({ db, userRepository, enrollmentRepository, paymentRepository });

  // App + rotas (todas sob /api, preservando os paths originais)
  const app = express();
  app.use(express.json());
  app.use('/api', checkoutRoutes(checkoutController(checkoutService)));
  app.use('/api', reportRoutes(reportController(reportService)));
  app.use('/api', userRoutes(userController(userService)));

  // 404 catch-all: rota desconhecida responde JSON (antes vazava o HTML default do Express).
  app.use((req, res, next) => next(new NotFoundError('Rota não encontrada')));
  app.use(errorHandler);
  return app;
}

async function main() {
  const app = await createApp();
  app.listen(settings.port, () => {
    console.log(`LMS API rodando na porta ${settings.port}...`);
  });
}

if (require.main === module) {
  main();
}

module.exports = { createApp };
