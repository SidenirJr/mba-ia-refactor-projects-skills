const { NotFoundError } = require('../errors');

class UserService {
  constructor(deps) {
    this.db = deps.db;
    this.users = deps.userRepository;
    this.enrollments = deps.enrollmentRepository;
    this.payments = deps.paymentRepository;
  }

  // Deleta o usuário e suas dependências em transação — corrige o "deixa sujo no banco".
  // Usuário inexistente é 404 (antes respondia 200 com `deleted:false`, contradizendo a mensagem).
  async delete(id) {
    return this.db.transaction(async () => {
      await this.payments.deleteByUserId(id);
      await this.enrollments.deleteByUserId(id);
      const { changes } = await this.users.deleteById(id);
      if (changes === 0) throw new NotFoundError('Usuário não encontrado');
      return { deleted: true };
    });
  }
}

module.exports = UserService;
