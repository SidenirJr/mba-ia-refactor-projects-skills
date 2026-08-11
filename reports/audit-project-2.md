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
File: AppManager.js:18
Description: `INSERT INTO users (...) VALUES ('Leonan', ..., '123')`; coluna `pass` é TEXT plano.
Impact: Credencial em texto puro no banco.
Recommendation: Hashear no seed. Playbook P4.

### [CRITICAL] God Class
File: AppManager.js:4-141
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
Recommendation: Abstração `PaymentGateway.charge()` (stub de sandbox isolado, sem logar segredos). Playbook P6/P12.

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
File: AppManager.js:28-137
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
Recommendation: Nomes descritivos (preservando o contrato externo dos campos).

### [LOW] Mistura de `this` e `self`
File: AppManager.js:26, 54, 57
Description: `const self = this` e uso misturado de `this.db`/`self.db` por causa de arrow vs function.
Recommendation: Padronizar com async/await (elimina o problema).

### [LOW] Código morto / exports enganosos
File: utils.js:2-5, 10, 25; AppManager.js:2
Description: `totalRevenue` exportado mas nunca atualizado/usado; `dbUser/dbPass/smtpUser` nunca referenciados (config morta que ainda vaza segredos).
Recommendation: Remover.

### [LOW] Magic numbers e loop inútil
File: utils.js:6, 19, 22
Description: `port: 3000` fixo; loop de 10000 iterações cujo resultado é descartado exceto 10 chars.
Recommendation: Config por env; remover loop inútil ao trocar o hashing.

================================
Total: 21 findings
================================

> Observação: as queries já usam placeholders `?` (sem SQL injection). Os riscos críticos
> aqui são exposição de segredos/cartão, hashing fraco, God Class e broken access control.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (autorizado via aprovação do plano e da abordagem de segurança)
