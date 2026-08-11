# 02 — Catálogo de Anti-Patterns (Fase 2)

Cada entrada tem: **sinais de detecção acionáveis** (o que procurar no código),
**severidade** e **por que importa**. Severidade segue a escala do desafio:

- **CRITICAL** — falha grave de arquitetura/segurança: impede funcionamento correto, expõe
  dados sensíveis (credenciais hardcoded, SQL Injection) ou viola completamente a separação
  de responsabilidades (God Class com DB + lógica + roteamento).
- **HIGH** — forte violação de MVC/SOLID que dificulta muito manutenção/testes (lógica de
  negócio pesada no controller, acoplamento forte sem DI, estado global mutável).
- **MEDIUM** — padronização/duplicação/performance moderada (N+1, middleware inadequado,
  validação ausente nas rotas).
- **LOW** — legibilidade, nomenclatura ruim, magic numbers.

> Mínimo exigido: detectar ≥8 destes anti-patterns. O catálogo abaixo tem ~20 + uma seção de
> APIs deprecated. Use o que se aplicar; nem todo projeto tem todos.

---

## CRITICAL

### C1. Hardcoded Secrets / Credentials
**Sinais:** strings com `SECRET_KEY`, `password`, `api_key`, `token`, `pk_live_`,
connection strings com usuário/senha, credenciais SMTP, atribuídas literalmente no código
(`app.config["SECRET_KEY"] = "..."`, `email_password = 'senha123'`, `dbPass: "..."`).
**Por que:** segredo versionado vaza para qualquer um com acesso ao repositório.
**Fix:** playbook P1.

### C2. SQL Injection (query montada por concatenação/interpolação)
**Sinais:** `cursor.execute("... " + var)`, f-strings/template strings com input do usuário
dentro de SQL (`f"SELECT * FROM t WHERE id = {id}"`, `"... WHERE email = '" + email + "'"`).
**Por que:** permite ler/alterar/destruir o banco e burlar autenticação.
**Fix:** playbook P2.

### C3. God Class / God File / God Method
**Sinais:** um arquivo/classe que concentra conexão de DB, criação de schema, seed,
roteamento, lógica de negócio e formatação ao mesmo tempo; arquivos muito longos com
responsabilidades heterogêneas; um `app.py` que também executa SQL direto.
**Por que:** impossível testar em isolamento; qualquer mudança afeta tudo.
**Fix:** playbook P3.

### C4. Weak / Plaintext Password Storage
**Sinais:** senha salva como texto puro; `hashlib.md5(...)`/`sha1(...)` sem salt; "crypto"
caseiro (loops de base64/substring); comparação direta `senha == row["senha"]`.
**Por que:** vazamento do banco compromete todas as contas; MD5/SHA1 são quebrados.
**Fix:** playbook P4.

### C5. Sensitive Data Exposure (resposta ou log)
**Sinais:** `senha`/`password`/hash em payload de resposta (`to_dict` que inclui senha,
`SELECT *` que devolve a coluna de senha); `console.log`/`print` de cartão de crédito,
chave de gateway, segredo; `/health` que devolve `secret_key`.
**Por que:** vaza dados sensíveis para o cliente/observabilidade (PCI-DSS, LGPD).
**Fix:** playbook P5.

### C6. Debug Mode / Interactive Debugger Exposto
**Sinais:** `debug=True` em `app.run(...)`, `DEBUG=True` em config, stack traces detalhados
ao cliente, ambiente marcado como produção com debug ligado.
**Por que:** o console interativo do Werkzeug/afins permite execução remota de código (RCE).
**Fix:** playbook P1 (config por env; debug nunca hardcoded).

### C7. Broken Access Control (endpoint perigoso sem auth)
**Sinais:** endpoints de admin/manutenção sem autenticação: reset de banco, execução de SQL
arbitrário, relatórios financeiros, delete de qualquer recurso por id sem verificação.
**Por que:** qualquer um executa ações destrutivas ou lê dados restritos.
**Fix:** playbook P12 (guard de auth, mantendo o endpoint vivo).

---

## HIGH

### H1. Business Logic in Controllers / Routes
**Sinais:** cálculos de domínio, regras de negócio, orquestração de notificações, montagem
de relatórios e decisões de pagamento **dentro** do handler HTTP/rota.
**Por que:** lógica presa ao transporte HTTP — não reutilizável, difícil de testar.
**Fix:** playbook P6.

### H2. No Dependency Injection / Tight Coupling
**Sinais:** módulos importam dependências concretas e globais (`import db`,
`new SqliteDb()` dentro do construtor), sem interfaces/abstração; impossível substituir o DB
por um fake em teste.
**Por que:** acoplamento estático impede teste e substituição.
**Fix:** playbook P7.

### H3. Mutable Global State
**Sinais:** variáveis mutáveis de módulo (`globalCache = {}`, `totalRevenue = 0`,
conexão singleton global mutável), caches em memória que crescem sem limite.
**Por que:** estado compartilhado entre requisições → race conditions e vazamento de memória.
**Fix:** playbook P7 (escopo por requisição / injeção).

### H4. Missing Transaction (escrita multi-passo não atômica)
**Sinais:** vários `INSERT`/`UPDATE` em sequência (criar pedido + itens + baixar estoque;
matrícula + pagamento + log) com um único commit no fim e sem `try/rollback`.
**Por que:** falha no meio deixa dados parciais/inconsistentes.
**Fix:** playbook P8.

### H5. Fake / Forgeable Auth Token
**Sinais:** "token" previsível como `'fake-jwt-token-' + user.id`, sem assinatura nem
expiração; autorização baseada em prefixo de cartão (`card.startsWith("4")`).
**Por que:** trivial de forjar/burlar.
**Fix:** playbook P12 (token assinado / abstração de autorização).

---

## MEDIUM

### M1. N+1 Queries
**Sinais:** loop que dispara uma query por item (`for pedido: query itens; for item: query
produto`), `len(u.tasks)` em loop, `.get()` por id dentro de iteração.
**Por que:** explode o número de idas ao banco; degrada performance linearmente.
**Fix:** playbook P9.

### M2. Missing / Weak Input Validation
**Sinais:** uso direto de `request.get_json()`/`req.body` sem checar presença/tipo;
`int(x)` sem guard; ausência de validação de formato (email, datas), de faixas e de
estrutura; `if preco_min:` que descarta `0` (bug de falsy).
**Por que:** 500s, dados inválidos no banco, comportamento inesperado.
**Fix:** playbook P10 (schema/validação centralizada).

### M3. Code Duplication
**Sinais:** blocos quase idênticos (mapeamento row→dict repetido, validação copiada entre
create/update, lógica de "overdue" repetida várias vezes), helpers/constantes existentes
porém ignorados e reimplementados inline.
**Por que:** manutenção multiplicada; correções esquecidas em cópias.
**Fix:** playbook P6/P10 (extrair para service/helper; reutilizar o que já existe).

### M4. Improper Middleware / Open CORS / Missing Hardening
**Sinais:** `CORS(app)` liberando todas as origens (inclusive admin/login); ausência de
error handler central; sem `helmet`/limites de body/rate limit; cada handler repete
`try/except → 500`.
**Por que:** superfície de ataque ampla e tratamento de erro inconsistente.
**Fix:** playbook P10/P11 (middleware central) e config de CORS restritiva.

### M5. No Pagination
**Sinais:** endpoints de listagem retornam a tabela inteira (`SELECT *` / `Model.query.all()`)
sem `limit/offset`/cursor.
**Por que:** não escala; risco de payloads gigantes.
**Fix:** parâmetros de paginação no controller/repository.

### M6. print()/console.log as Logging
**Sinais:** `print(...)`/`console.log(...)` para rastrear fluxo, erros e eventos de negócio.
**Por que:** sem níveis, sem estrutura, sem destino configurável.
**Fix:** playbook P11 (logger).

---

## LOW

### L1. Magic Numbers / Strings
**Sinais:** limites e taxas soltos no código (descontos `0.1/0.05`, faixas `10000/5000`,
tamanhos `2/200`), listas de status/categorias inline em vários lugares.
**Fix:** constantes nomeadas / config.

### L2. Bad Naming / Shadowing de builtin
**Sinais:** variáveis `u, e, p, cid, cc`, parâmetro `id` (sombreia builtin Python),
`type(x) == list` em vez de `isinstance`.
**Fix:** nomes descritivos; idioms da linguagem.

### L3. Dead Code / Unused Imports
**Sinais:** imports não usados, funções/classes/serviços nunca chamados, exports mortos,
dependências declaradas e nunca importadas.
**Fix:** remover.

---

## Seção especial — APIs Deprecated (obrigatória quando aplicável)

Detecte uso de APIs obsoletas e **recomende o equivalente moderno**. Sinais comuns:

| Deprecated (sinal no código) | Stack | Equivalente moderno |
|---|---|---|
| `Model.query.get(id)`, `Model.query...` (Query API) | SQLAlchemy 2.x / Flask-SQLAlchemy 3.1 | `db.session.get(Model, id)`, `db.session.execute(db.select(Model))` |
| `datetime.utcnow()` | Python 3.12+ | `datetime.now(datetime.UTC)` (timezone-aware) |
| `sqlite3` driver baseado em callbacks | Node | `node:sqlite`, `better-sqlite3`, ou wrapper `sqlite` com async/await |
| `body-parser` standalone | Express 4.16+ | `express.json()` / `express.urlencoded()` |
| pirâmide de callbacks de DB | Node | `async/await` + `Promise.all` |
| `var` | JS | `const`/`let` |
| `app.run(debug=True)` como entrypoint de produção | Flask | servidor WSGI (gunicorn) + debug por env |
| hashing caseiro / `md5`/`sha1` para senha | qualquer | `bcrypt`/`argon2`/`scrypt` ou `werkzeug.security` |
| `new Date()`/`Date.now()` para lógica de negócio sem timezone | JS | datas timezone-aware |

Reporte cada uso como finding com a severidade apropriada (a maioria é MEDIUM; hashing
fraco é CRITICAL) e a linha exata, citando o equivalente moderno na recomendação.
