class UserService {
  constructor(deps) {
    this.db = deps.db;
    this.users = deps.userRepository;
    this.enrollments = deps.enrollmentRepository;
    this.payments = deps.paymentRepository;
  }

  // Deleta o usuário e suas dependências em transação — corrige o "deixa sujo no banco".
  async delete(id) {
    return this.db.transaction(async () => {
      await this.payments.deleteByUserId(id);
      await this.enrollments.deleteByUserId(id);
      const { changes } = await this.users.deleteById(id);
      return { deleted: changes > 0 };
    });
  }
}

module.exports = UserService;
