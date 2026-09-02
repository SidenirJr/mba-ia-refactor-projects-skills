# ecommerce-api-legacy

LMS API (fluxo de checkout) em Node.js/Express. Originalmente uma **God Class** (`AppManager`);
**refatorada para MVC em camadas** pela skill `refactor-arch`.

## Como rodar

```bash
npm install
cp .env.example .env        # PREENCHA ADMIN_TOKEN e PAYMENT_GATEWAY_KEY (obrigatórios)
npm start
```

Ou exportando as variáveis direto no shell:

```bash
export ADMIN_TOKEN="$(openssl rand -hex 32)"
export PAYMENT_GATEWAY_KEY="sua-chave-do-gateway"
npm start
```

`ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` **não têm valor default** — nenhum segredo é versionado no
repositório. Sem essas variáveis a aplicação **falha na inicialização** com a mensagem
`[config] Configuração obrigatória ausente: ...` e código de saída 1, em vez de subir com um token
público que qualquer leitor do repositório conheceria.

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e carrega seeds no boot
(senha do seed **hasheada**). Exemplos de requisições em `api.http` (o token é lido do ambiente,
não está escrito no arquivo).

## Estrutura (MVC)

```
src/
├── app.js                  # composition root (bootstrap async + injeção de dependência)
├── config/                 # settings (env via dotenv) + database (wrapper async + schema/seed)
├── models/                 # repositories (queries parametrizadas)
├── services/               # checkout (transacional), relatório, usuário, paymentGateway, passwordHasher
├── controllers/            # handlers HTTP finos
├── routes/                 # routers por recurso (preservam os paths /api/*)
├── middlewares/            # admin guard, error handler, asyncHandler
└── errors.js               # erros de domínio
```

## Endpoints

| Método | Path | Observação |
|---|---|---|
| POST | `/api/checkout` | corpo: `usr, eml, pwd, c_id, card` (contrato preservado) |
| GET | `/api/admin/financial-report` | exige header `X-Admin-Token` |
| DELETE | `/api/users/:id` | exige header `X-Admin-Token`; deleta em cascata; **404** se o usuário não existe |

Rota desconhecida responde `404` em JSON (`{"erro":"Rota não encontrada"}`), não o HTML default do
Express. Erros `5xx` respondem `{"erro":"Erro interno no servidor"}` — o detalhe técnico fica apenas
no log do servidor.

### Cartão no checkout

`card` aceita string (`"4242424242424242"`) ou número JSON (`4242424242424242`). A aprovação exige
PAN estruturalmente válido: checksum de Luhn e 13 a 19 dígitos (faixa real de PAN). Uma cobrança
aprovada cujo registro no banco falhe é **estornada automaticamente** (compensação registrada em log).

Variáveis de ambiente em `.env.example`; `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` são obrigatórias em
qualquer ambiente.
