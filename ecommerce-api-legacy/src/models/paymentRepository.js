class PaymentRepository {
  constructor(db) {
    this.db = db;
  }

  create(enrollmentId, amount, status) {
    return this.db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status],
    );
  }

  deleteByUserId(userId) {
    return this.db.run(
      'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
      [userId],
    );
  }
}

module.exports = PaymentRepository;
