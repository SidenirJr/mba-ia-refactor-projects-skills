/**
 * Abstração de gateway de pagamento.
 *
 * STUB de sandbox isolado do handler HTTP e SEM logar o número do cartão (PAN) nem a
 * chave do gateway. A decisão de aprovação é uma verificação real, não uma heurística
 * de bandeira: (1) o número precisa ser um cartão estruturalmente válido (checksum de
 * Luhn) — recusa qualquer entrada malformada, não só "algo que não comece com 4"; (2)
 * dentre os cartões válidos, uma pequena lista de números de teste conhecidos simula
 * recusas do emissor (mesma convenção usada por gateways reais em modo sandbox, ex.:
 * Stripe). Qualquer outro cartão Luhn-válido é aprovado. Em produção, troque `charge`
 * por uma chamada real ao provedor usando `this.apiKey`.
 */

// Cartões de teste que o "emissor" simulado sempre recusa (Luhn-válidos, mas reservados
// para exercitar o caminho de recusa — mesma convenção de gateways reais em sandbox).
const DECLINED_TEST_CARDS = new Set([
  '4000000000000002', // recusa genérica do emissor
  '4000000000009995', // saldo insuficiente
]);

function onlyDigits(value) {
  return typeof value === 'string' ? value.replace(/\D/g, '') : '';
}

function isLuhnValid(card) {
  const digits = onlyDigits(card);
  if (digits.length < 12 || digits.length > 19) return false;
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
    return { status: 'PAID', amount };
  }
}

module.exports = PaymentGateway;
