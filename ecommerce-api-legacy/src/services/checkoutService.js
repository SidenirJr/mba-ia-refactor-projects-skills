const crypto = require('crypto');

const { ValidationError, NotFoundError, PaymentError } = require('../errors');

class CheckoutService {
  constructor(deps) {
    this.db = deps.db;
    this.users = deps.userRepository;
    this.courses = deps.courseRepository;
    this.enrollments = deps.enrollmentRepository;
    this.payments = deps.paymentRepository;
    this.audit = deps.auditLogRepository;
    this.gateway = deps.paymentGateway;
    this.hasher = deps.passwordHasher;
  }

  async execute({ name, email, password, courseId, card }) {
    if (!name || !email || !courseId || !card) {
      throw new ValidationError('Bad Request');
    }

    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    // Autoriza o pagamento ANTES de qualquer escrita — evita usuário/matrícula órfãos
    // quando o pagamento é recusado (bug do código original).
    const payment = await this.gateway.charge(card, course.price);
    if (payment.status === 'DENIED') throw new PaymentError('Pagamento recusado');

    // Criação de usuário (se necessário) + matrícula + pagamento + auditoria, atomicamente.
    return this.db.transaction(async () => {
      let userId;
      const existing = await this.users.findByEmail(email);
      if (existing) {
        userId = existing.id;
      } else {
        // sem default fraco "123456": gera senha aleatória quando não informada
        const plain = password || crypto.randomBytes(12).toString('hex');
        userId = await this.users.create(name, email, this.hasher.hash(plain));
      }

      const enrollmentId = await this.enrollments.create(userId, courseId);
      await this.payments.create(enrollmentId, course.price, payment.status);
      await this.audit.create(`Checkout curso ${courseId} por ${userId}`);
      return { msg: 'Sucesso', enrollment_id: enrollmentId };
    });
  }
}

module.exports = CheckoutService;
