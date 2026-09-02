# code-smells-project

API de E-commerce em Python/Flask. Originalmente um monólito de 4 arquivos com code smells
intencionais; **refatorado para MVC em camadas** pela skill `refactor-arch`.

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# SECRET_KEY e ADMIN_TOKEN são OBRIGATÓRIAS — a app não sobe sem elas
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ADMIN_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

python app.py
```

Alternativamente, copie `.env.example` para `.env` e preencha `SECRET_KEY` e `ADMIN_TOKEN`.
Para conveniência local você pode exportar `FLASK_ENV=development`: nesse caso, se as duas
variáveis estiverem ausentes, valores **aleatórios em memória** são gerados a cada boot
(logados no console e diferentes a cada reinício — nunca use em produção).

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas **hasheadas**).

## Estrutura (MVC)

```
app.py                       # entry point (python app.py) — também é o objeto WSGI
src/
├── app.py                   # composition root (app-factory + injeção de dependência)
├── config/settings.py       # configuração por ambiente (segredos obrigatórios, fail-fast)
├── models/                  # repositories com queries parametrizadas + schema/seed
│   ├── database.py
│   ├── produto_repository.py
│   ├── usuario_repository.py
│   ├── pedido_repository.py
│   ├── admin_repository.py  # SQL dos endpoints /admin/* (execução somente-leitura)
│   └── system_repository.py # SQL do health check
├── services/                # regras de negócio (validação, total/estoque, descontos, auth)
│   ├── auth_token_service.py # emissão/verificação do token de sessão assinado
│   ├── authorization.py      # regras de dono/papel (recebem o usuário atual por parâmetro)
│   ├── admin_service.py      # validação da consulta administrativa (allowlist)
│   └── system_service.py
├── controllers/             # handlers HTTP finos (sem SQL)
├── views/routes.py          # roteamento + política de autorização por rota
├── middlewares/             # error handler central + guards de autenticação
└── errors.py                # exceções de domínio
```

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `SECRET_KEY` | **sim** | — | Assina os tokens de sessão. Sem ela a app aborta o boot. |
| `ADMIN_TOKEN` | **sim** | — | Valor esperado no header `X-Admin-Token` dos endpoints `/admin/*`. Sem ela a app aborta o boot. |
| `FLASK_ENV` | não | `production` | Com `development`, gera segredos aleatórios em memória quando ausentes. |
| `TOKEN_MAX_AGE` | não | `86400` | Validade do token de sessão, em segundos. |
| `DEBUG` | não | `false` | Modo debug do Flask. |
| `DB_PATH` | não | `loja.db` | Caminho do SQLite. |
| `CORS_ORIGINS` | não | `*` | Origens permitidas. |
| `HOST` / `PORT` | não | `0.0.0.0` / `5000` | Bind do servidor. |

Em produção, defina `SECRET_KEY`, `ADMIN_TOKEN` e `DEBUG=false`.

## Autenticação e autorização

`POST /login` devolve, além dos dados do usuário, um **token de sessão assinado**
(`itsdangerous.URLSafeTimedSerializer`). Envie-o nas rotas protegidas:

```bash
TOKEN=$(curl -s -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["dados"]["token"])')

curl -s localhost:5000/pedidos -H "Authorization: Bearer $TOKEN"
```

O usuário é recarregado do banco em cada requisição — um usuário removido perde o acesso
imediatamente, mesmo com token ainda válido.

### Política por rota

| Acesso | Endpoints |
|---|---|
| Público | `GET /`, `GET /health`, `POST /login`, `POST /usuarios`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>` |
| Autenticado | `POST /pedidos` (o dono é sempre o usuário do token), `GET /pedidos/usuario/<id>` e `GET /usuarios/<id>` (próprio usuário ou admin) |
| Admin (`tipo = admin`) | `POST/PUT/DELETE /produtos`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas` |
| Admin **+** header `X-Admin-Token` | `POST /admin/query`, `POST /admin/reset-db` |

Sem token → `401`; autenticado sem permissão → `403`.

### `POST /admin/query`

O endpoint continua existindo, mas aceita apenas **uma instrução `SELECT`** sobre as
tabelas `produtos`, `usuarios`, `pedidos` e `itens_pedido`. São recusadas com `400`:
múltiplas instruções, comentários SQL (`--`, `/* */`), qualquer palavra-chave de
escrita/DDL (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, …), `PRAGMA`,
`ATTACH`/`DETACH` e referências a tabelas fora da allowlist. A coluna `senha` nunca é
retornada. A execução ainda passa por um *authorizer* somente-leitura do SQLite.
