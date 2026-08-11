/**
 * Abstração de gateway de pagamento.
 *
 * A implementação atual é um STUB de sandbox que aprova cartões iniciados em "4"
 * (preservando o comportamento externo do projeto original), porém isolada do handler
 * HTTP e SEM logar o número do cartão (PAN) nem a chave do gateway. Em produção,
 * troque `charge` por uma chamada real ao provedor usando `this.apiKey`.
 */
class PaymentGateway {
  constructor(apiKey) {
    this.apiKey = apiKey; // usado pela integração real; nunca logado
  }

  async charge(card, amount) {
    const approved = typeof card === 'string' && card.startsWith('4');
    return { status: approved ? 'PAID' : 'DENIED', amount };
  }
}

module.exports = PaymentGateway;
