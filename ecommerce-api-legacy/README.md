# ecommerce-api-legacy

LMS API (fluxo de checkout) em Node.js/Express. Originalmente uma **God Class** (`AppManager`);
**refatorada para MVC em camadas** pela skill `refactor-arch`.

## Como rodar

```bash
npm install
cp .env.example .env        # ajuste os valores (opcional em dev)
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e carrega seeds no boot
(senha do seed **hasheada**). Exemplos de requisições em `api.http`.

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
| DELETE | `/api/users/:id` | exige header `X-Admin-Token`; agora deleta em cascata |

Variáveis de ambiente em `.env.example`. Em produção defina `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY`.
