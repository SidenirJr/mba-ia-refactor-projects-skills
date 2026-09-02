```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js, CommonJS)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6 (sem dotenv, helmet, test runner ou linter)
Domain:        LMS / e-commerce de cursos — fluxo de checkout (matrícula + pagamento)
Architecture:  God Class — AppManager concentra DB, schema, seed, rotas, lógica e pagamento
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 6 | HIGH: 6 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Segredos hardcoded no código
File: utils.js:2-5
Description: `dbUser`, `dbPass` ("senha_super_secreta_prod_123"), `paymentGatewayKey` ("pk_live_...") e `smtpUser` literais no fonte.
Impact: Segredos de produção versionados; chave `pk_live_` é de gateway real.
Recommendation: Mover para variáveis de ambiente (.env + dotenv); remover do código. Playbook P1.

### [CRITICAL] Cartão de crédito e chave do gateway logados
File: AppManager.js:45
Description: `console.log("Processando cartão ${cc} na chave ${config.paymentGatewayKey}")` grava PAN completo e a chave secreta.
Impact: Violação de PCI-DSS; vazamento de cartão e segredo nos logs.
Recommendation: Nunca logar PAN/segredo; isolar pagamento atrás de uma abstração de gateway. Playbook P5.

### [CRITICAL] Hashing de senha caseiro e inseguro
File: utils.js:17-23
Description: `badCrypto` concatena base64 em loop e trunca em 10 chars — determinístico, sem salt, não é hash real.
Impact: Senhas trivialmente quebráveis; vazamento do banco compromete contas.
Recommendation: KDF real (`crypto.scrypt`/bcrypt/argon2) com salt por usuário. Playbook P4.

### [CRITICAL] Senha em texto puro no seed
File: AppManager.js:12, 18
Description: `INSERT INTO users (...) VALUES ('Leonan', ..., '123')`; coluna `pass` é TEXT plano.
Impact: Credencial em texto puro no banco.
Recommendation: Hashear no seed. Playbook P4.

### [CRITICAL] God Class
File: AppManager.js:4-139
Description: Uma classe faz conexão de DB, schema, seed, roteamento, controllers, regra de pagamento e relatório.
Impact: Impossível testar/isolar; qualquer mudança afeta tudo.
Recommendation: Quebrar em config, repositories, services, controllers, routes, middlewares. Playbook P3.

### [CRITICAL] Broken access control em endpoints sensíveis
File: AppManager.js:80, 131
Description: `GET /api/admin/financial-report` (toda a receita + alunos) e `DELETE /api/users/:id` sem autenticação.
Impact: Qualquer um lê dados financeiros e deleta usuários.
Recommendation: Guard de admin (token via env), mantendo os endpoints vivos. Playbook P12.

### [HIGH] Autorização de pagamento fake
File: AppManager.js:46
Description: `let status = cc.startsWith("4") ? "PAID" : "DENIED"` — aprova pagamento pela bandeira do cartão, sem gateway real.
Impact: Lógica de pagamento fictícia e acoplada ao handler.
Recommendation: Abstração `PaymentGateway.charge()` isolada do handler **e** verificação real
dentro dela (checksum estrutural + casos de teste determinísticos) — mover o código para uma
classe sem trocar a heurística não resolve o finding. Playbook P3/P6 (extrair) + **P14**
(verificação real). Catálogo: H6.

### [HIGH] Escrita multi-passo sem transação
File: AppManager.js:50-63
Description: Inserts de enrollment, payment e audit em sequência, sem transação; falha no meio deixa matrícula órfã sem pagamento.
Impact: Inconsistência de dados.
Recommendation: Envolver em transação (BEGIN/COMMIT/ROLLBACK). Playbook P8.

### [HIGH] Usuário órfão em pagamento recusado
File: AppManager.js:66-75, 43-48
Description: O usuário é criado ANTES da checagem de pagamento; cartão recusado retorna 400 deixando o usuário sem matrícula.
Impact: Dados parciais; usuários "fantasma".
Recommendation: Autorizar pagamento antes de qualquer escrita e tudo em transação. Playbook P8.

### [HIGH] Delete sem cascata / integridade
File: AppManager.js:131-136
Description: Deleta o usuário mas deixa enrollments/payments pendurados; ignora `err` e responde 200 mesmo em falha (a própria resposta admite "ficaram sujos no banco").
Impact: Registros órfãos; erros silenciados.
Recommendation: Deletar dependências em transação; tratar erro. Playbook P8/P10.

### [HIGH] Estado global mutável
File: utils.js:9-15
Description: `globalCache = {}` (cresce sem limite via `logAndCache`) e `totalRevenue = 0` compartilhados no módulo.
Impact: Vazamento de memória e estado compartilhado entre requisições.
Recommendation: Eliminar globais mutáveis; escopo por requisição/serviço. Playbook P7.

### [HIGH] Lógica de negócio nos handlers, sem DI
File: AppManager.js:7, 28-137
Description: Checkout, relatório e delete inline nas rotas; DB fixado no construtor (`new sqlite3.Database`), sem injeção.
Impact: Não testável, fortemente acoplado.
Recommendation: Controllers finos → services → repositories injetados. Playbook P6/P7.

### [MEDIUM] Queries N+1 no relatório financeiro
File: AppManager.js:83-127
Description: Para cada curso, query de enrollments; para cada enrollment, query de user e de payment.
Impact: Explosão de consultas; não escala.
Recommendation: Uma query com JOIN agregando por curso. Playbook P9.

### [MEDIUM] Coordenação assíncrona manual e frágil
File: AppManager.js:86-122
Description: Contadores `coursesPending`/`enrPending` para detectar término em vez de `Promise.all`.
Impact: Propenso a race conditions; ilegível.
Recommendation: async/await + Promise.all. Playbook P11.

### [MEDIUM] Validação de entrada incompleta
File: AppManager.js:35
Description: Valida `u,e,cid,cc` mas não a senha; sem validação de formato de email, de `c_id` numérico, nem do cartão.
Impact: 500s e dados inválidos.
Recommendation: Validação centralizada. Playbook P10.

### [MEDIUM] Erros engolidos e contrato de resposta inconsistente
File: AppManager.js:92, 104, 106, 133; 35, 60, 135
Description: Parâmetro `err` ignorado em várias queries; respostas misturam texto puro e JSON; sem error handler central.
Impact: Falhas silenciosas; respostas inconsistentes.
Recommendation: Error handler central + envelope de erro padronizado. Playbook P10.

### [MEDIUM] API deprecated: driver sqlite3 por callbacks (callback hell)
File: AppManager.js:1, 37-77, 83-127
Description: Uso do `sqlite3` com pirâmide de callbacks aninhados.
Impact: Código frágil e difícil de manter.
Recommendation: Wrapper com Promises + async/await (equivalente moderno: `node:sqlite`/`better-sqlite3`). Playbook P11.

### [LOW] Nomenclatura críptica
File: AppManager.js:29-33
Description: Variáveis `u, e, p, cid, cc` e chaves de request não padronizadas `usr, eml, pwd, c_id, card`.
Impact: O handler de checkout só é legível relendo a desestruturação — `e` (email) e `p` (senha) são indistinguíveis à leitura, e trocá-los em uma chamada não gera erro de sintaxe, apenas grava dado errado.
Recommendation: Nomes descritivos (preservando o contrato externo dos campos).

### [LOW] Mistura de `this` e `self`
File: AppManager.js:26, 54, 57
Description: `const self = this` e uso misturado de `this.db`/`self.db` por causa de arrow vs function.
Impact: Converter um callback de `function` para arrow (ou o inverso) muda silenciosamente a quem `this` se refere; o erro só aparece em runtime, como `this.db is undefined`, e apenas na rota afetada.
Recommendation: Padronizar com async/await (elimina o problema).

### [LOW] Código morto / exports enganosos
File: utils.js:2-5, 10, 25; AppManager.js:2
Description: `totalRevenue` exportado mas nunca atualizado/usado; `dbUser/dbPass/smtpUser` nunca referenciados (config morta que ainda vaza segredos).
Impact: `totalRevenue` é um número que aparenta ser receita acumulada e vale sempre 0 — quem importá-lo produz relatório errado sem nenhum erro; e `dbPass`/`smtpUser` mantêm segredos versionados que não sustentam nem uma funcionalidade.
Recommendation: Remover.

### [LOW] Magic numbers e loop inútil
File: utils.js:6, 19, 22
Description: `port: 3000` fixo; loop de 10000 iterações cujo resultado é descartado exceto 10 chars.
Impact: A porta fixa impede subir duas instâncias ou respeitar o `PORT` do ambiente de deploy; o loop queima CPU a cada hash de senha sem adicionar nenhuma segurança (o resultado é truncado em 10 chars de base64).
Recommendation: Config por env; remover loop inútil ao trocar o hashing.

================================
Total: 21 findings
================================

> Observação: as queries já usam placeholders `?` (sem SQL injection). Os riscos críticos
> aqui são exposição de segredos/cartão, hashing fraco, God Class e broken access control.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (autorizado via aprovação do plano e da abordagem de segurança)

================================
ADENDO — 2026-09-02 (revisão do professor)
================================
Achado: a Fase 3 original moveu `cc.startsWith("4") ? "PAID" : "DENIED"` de `AppManager.js`
para `src/services/paymentGateway.js` — resolvendo a parte arquitetural do finding [HIGH]
"Autorização de pagamento fake" (God Class → classe isolada, sem logar PAN/chave) — mas manteve
a heurística de bandeira **idêntica**. O impacto descrito no próprio finding ("lógica de
pagamento fictícia") continuava de pé: qualquer cartão iniciado em "4" era aprovado, mesmo sem
ser um número de cartão válido.

Causa raiz na skill: o catálogo (`02-antipattern-catalog.md`, H5) agrupava "token de auth
forjável" e "autorização por prefixo de cartão" sob o mesmo sinal, apontando para o mesmo fix
(guard de sessão) — mas validar *quem é o usuário* (P13) e validar *se uma operação de negócio
é legítima* (pagamento) são problemas diferentes; reorganizar o código sem trocar a lógica não
fecha nenhum dos dois.

Correção na skill: novo anti-pattern **H6 — Fake Business/Domain Verification**, separado de
H5, cobrindo decisões de negócio (pagamento, crédito, elegibilidade) decididas por heurística
sem relação real com a verificação devida. Novo Playbook **P14**: verificação estrutural real
(checksum de Luhn) + lista determinística e pequena de casos de teste conhecidos para os
caminhos de erro — mesma convenção usada por gateways reais em modo sandbox (Stripe etc.). A
Fase 3 do `SKILL.md` foi reforçada: mover uma verificação fake para uma classe/service sem
trocar a lógica não fecha o finding.

Correção no código: `src/services/paymentGateway.js` agora valida o número do cartão pelo
checksum de Luhn (rejeita qualquer entrada estruturalmente inválida, não só "o que não começa
com 4") e usa uma lista fixa de cartões de teste (`4000000000000002`, `4000000000009995`) para
simular recusas do emissor — mesma convenção de sandbox de gateways reais. `api.http` atualizado
com números de teste realmente válidos (Luhn) para os exemplos de sucesso/recusa.

Validação (requisições reais, servidor no ar): cartão "bandeira Visa" mas Luhn-inválido
(`4000000000000001`) → **400, recusado** (antes seria sempre aprovado só pelo prefixo); cartão
de teste na denylist (`4000000000000002`, Luhn-válido) → **400, recusado**; cartão de teste
válido (`4242424242424242`) → **200, aprovado**; cartão "bandeira Mastercard" mas Luhn-válido
(`5555555555554444`) → **200, aprovado** (antes seria sempre recusado só pelo prefixo — prova de
que a decisão não depende mais da bandeira). Regressão nos demais endpoints (checkout normal,
`/admin/financial-report` com/sem token, `DELETE /users/:id` sem token) sem mudanças: 4/4 OK.

================================
ADENDO — 2026-09-02 (remediação de segredos/concorrência e correções deste relatório)
================================
Correções neste relatório, sem alterar nenhum finding de mérito: a contagem já estava correta
(`CRITICAL: 6 | HIGH: 6 | MEDIUM: 5 | LOW: 4` = `Total: 21 findings`, conferido contra os
cabeçalhos `### [SEV]` reais). Referências reconciliadas com a linha-base: God Class
`AppManager.js:4-141` → `4-139` (a classe fecha em 139; 141 é o `module.exports`); "Lógica de
negócio nos handlers, sem DI" `28-137` → `7, 28-137` (o `new sqlite3.Database(':memory:')`
citado na descrição está na linha 7, no construtor); "Senha em texto puro no seed" `18` →
`12, 18` (a afirmação de que a coluna `pass` é TEXT plano vem do `CREATE TABLE users` na linha
12). Adicionado o campo obrigatório `Impact:` aos 4 findings LOW, que estavam sem ele.

Remediação aplicada no código nesta rodada:

- `ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` não têm mais fallback hardcoded — o antigo default
  `dev-admin-token-change-me` era o mesmo token publicado no `api.http`. A aplicação agora sai
  com código 1 e mensagem clara se as variáveis não vierem do ambiente. O comentário que
  afirmava "nenhum segredo hardcoded no código" foi corrigido e o `api.http` passou a usar
  `{{$processEnv ADMIN_TOKEN}}`. **O token antigo deve ser considerado comprometido** —
  verificado que ele agora recebe 401.
- `transaction()` passou a serializar o trabalho numa fila de promessas sobre a conexão sqlite3
  única, e o `BEGIN` foi movido para dentro do `try` (antes uma falha no próprio `BEGIN` não
  disparava `ROLLBACK`). Verificado: 10 checkouts concorrentes retornaram 10× HTTP 200, contra
  9× HTTP 500 (`SQLITE_ERROR: cannot start a transaction within a transaction`) antes da
  correção. Integridade pós-teste conferida pelo relatório financeiro: 12 alunos, 12 pagamentos,
  nenhuma matrícula sem pagamento.
- Compensação de cobrança implementada: se a persistência falhar depois de a cobrança já ter
  sido aprovada, o valor é estornado no gateway (`refund(transactionId, amount)`) e o fato é
  logado, incluindo log crítico de conciliação manual caso o próprio estorno falhe. Verificado
  forçando falha de persistência: o cliente recebeu 500 genérico, o log registrou o estorno
  bem-sucedido e o usuário criado dentro da transação não persistiu.
- O error handler deixou de devolver `err.message` cru em status >= 500: responde
  `{"erro":"Erro interno no servidor"}` e loga método, URL e erro completo no servidor.
  Verificado que o texto `SQLITE_ERROR` aparece apenas no log.
- Adicionado 404 em JSON para rota desconhecida (antes retornava o HTML default do Express).
- `DELETE /api/users/:id` com id inexistente passou de 200 `{"deleted":false}` para 404
  `{"erro":"Usuário não encontrado"}`.
- `card` no checkout passou a aceitar número JSON além de string, e o comprimento de PAN foi
  restringido a 13-19 dígitos (antes 12 dígitos era aceito).

MUDANÇAS DE CONTRATO (registro explícito): (1) delete de id inexistente 200 → 404; (2) o corpo
dos erros 5xx passa a ser genérico; (3) rota desconhecida passa a devolver JSON; (4)
`ADMIN_TOKEN` e `PAYMENT_GATEWAY_KEY` tornam-se obrigatórios na inicialização; (5) PAN de 12
dígitos passa a ser recusado.

Permanecem em aberto, fora do escopo desta rodada: helmet/rate-limiting, idempotência do
checkout, verificação de posse do e-mail no checkout, `crypto.timingSafeEqual` na comparação do
token de admin, e vulnerabilidades transitivas do `npm audit` em dependências do `sqlite3`.
