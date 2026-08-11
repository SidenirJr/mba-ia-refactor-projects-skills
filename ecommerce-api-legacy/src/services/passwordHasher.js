const crypto = require('crypto');

// KDF real (scrypt) com salt por usuário — substitui o `badCrypto` caseiro.
function hash(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const derived = crypto.scryptSync(String(password), salt, 64).toString('hex');
  return `${salt}:${derived}`;
}

function verify(password, stored) {
  if (!stored || !stored.includes(':')) return false;
  const [salt, key] = stored.split(':');
  const derived = crypto.scryptSync(String(password), salt, 64).toString('hex');
  const keyBuf = Buffer.from(key, 'hex');
  const derBuf = Buffer.from(derived, 'hex');
  return keyBuf.length === derBuf.length && crypto.timingSafeEqual(keyBuf, derBuf);
}

module.exports = { hash, verify };
