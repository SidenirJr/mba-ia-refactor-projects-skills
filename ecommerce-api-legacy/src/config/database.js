const sqlite3 = require('sqlite3').verbose();

const passwordHasher = require('../services/passwordHasher');

// Wrapper que expõe o driver sqlite3 (baseado em callbacks) via Promises/async-await,
// eliminando a pirâmide de callbacks e habilitando transações reais.
class Database {
  constructor(path) {
    this.db = new sqlite3.Database(path);
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function (err) {
        if (err) return reject(err);
        resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  async transaction(work) {
    await this.run('BEGIN');
    try {
      const result = await work();
      await this.run('COMMIT');
      return result;
    } catch (err) {
      await this.run('ROLLBACK');
      throw err;
    }
  }
}

async function initSchema(db) {
  await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
  await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
  await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

  const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
  if (count === 0) {
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      ['Leonan', 'leonan@fullcycle.com.br', passwordHasher.hash('123')]); // senha hasheada
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
      ['Clean Architecture', 997.00, 'Docker', 497.00]);
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
  }
}

module.exports = { Database, initSchema };
