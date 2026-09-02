const crypto = require('crypto');

/**
 * Abstração de gateway de pagamento.
 *
 * STUB de sandbox isolado do handler HTTP e SEM logar o número do cartão (PAN) nem a
 * chave do gateway. A decisão de aprovação é uma verificação real, não uma heurística
 * de bandeira: (1) o número precisa ser um cartão estruturalmente válido (checksum de
 * Luhn e comprimento de PAN entre 13 e 19 dígitos) — recusa qualquer entrada malformada,
 * não só "algo que não comece com 4"; (2) dentre os cartões válidos, uma pequena lista de
 * números de teste conhecidos simula recusas do emissor (mesma convenção usada por
 * gateways reais em modo sandbox, ex.: Stripe). Qualquer outro cartão Luhn-válido é
 * aprovado. Em produção, troque `charge`/`refund` por chamadas reais ao provedor usando
 * `this.apiKey`.
 */

// Cartões de teste que o "emissor" simulado sempre recusa (Luhn-válidos, mas reservados
// para exercitar o caminho de recusa — mesma convenção de gateways reais em sandbox).
const DECLINED_TEST_CARDS = new Set([
  '4000000000000002', // recusa genérica do emissor
  '4000000000009995', // saldo insuficiente
]);

// Faixa real de comprimento de um PAN (ISO/IEC 7812): 13 a 19 dígitos.
const PAN_MIN_DIGITS = 13;
const PAN_MAX_DIGITS = 19;

// Aceita o cartão como string ("4242...") ou como número JSON (4242424242424242, sem aspas).
function onlyDigits(value) {
  if (typeof value === 'string') return value.replace(/\D/g, '');
  if (typeof value === 'number' && Number.isInteger(value) && Number.isSafeInteger(value)) {
    return String(Math.abs(value));
  }
  return '';
}

function isLuhnValid(card) {
  const digits = onlyDigits(card);
  if (digits.length < PAN_MIN_DIGITS || digits.length > PAN_MAX_DIGITS) return false;
  let sum = 0;
  let double = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = digits.charCodeAt(i) - 48;
    if (double) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    double = !double;
  }
  return sum % 10 === 0;
}

class PaymentGateway {
  constructor(apiKey) {
    this.apiKey = apiKey; // usado pela integração real; nunca logado
  }

  async charge(card, amount) {
    if (!isLuhnValid(card)) {
      return { status: 'DENIED', reason: 'invalid_card_number', amount };
    }
    if (DECLINED_TEST_CARDS.has(onlyDigits(card))) {
      return { status: 'DENIED', reason: 'card_declined', amount };
    }
    // transactionId é o que permite compensar (estornar) a cobrança se a persistência falhar.
    return { status: 'PAID', amount, transactionId: `ch_${crypto.randomUUID()}` };
  }

  // Compensação da cobrança: usada quando a cobrança foi aprovada mas a matrícula não
  // pôde ser persistida (saga simples — sem isso o cartão fica cobrado sem contrapartida).
  async refund(transactionId, amount) {
    if (!transactionId) {
      throw new Error('refund exige o transactionId da cobrança original');
    }
    return { status: 'REFUNDED', transactionId, amount };
  }
}

module.exports = PaymentGateway;
