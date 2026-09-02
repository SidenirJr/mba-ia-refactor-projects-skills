# Solução — Skill `refactor-arch`

Skill do Claude Code que **audita e refatora** projetos de backend para o padrão **MVC**, de
forma **agnóstica de tecnologia**, em 3 fases: **Análise → Auditoria (com confirmação) →
Refatoração (com validação)**. Foi construída uma única vez e copiada, **sem alterações**, para
os 3 projetos (2 Python/Flask + 1 Node/Express), provando o agnosticismo.

- Skill: `*/.claude/skills/refactor-arch/` (`SKILL.md` + 5 arquivos de referência)
- Relatórios de auditoria: [`reports/audit-project-1.md`](reports/audit-project-1.md) ·
  [`reports/audit-project-2.md`](reports/audit-project-2.md) ·
  [`reports/audit-project-3.md`](reports/audit-project-3.md)
- Código refatorado: `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`

### Como ver o diff antes → depois

O código pré-refatoração é o do repositório base do desafio. Para inspecionar qualquer
`arquivo:linha` citado nos relatórios, ou o diff completo da refatoração:

```bash
git remote add upstream https://github.com/devfullcycle/mba-ia-refactor-projects-skill.git
git fetch upstream

# um arquivo original inteiro
git show 'upstream/main:code-smells-project/models.py'

# um finding específico (ex.: SECRET_KEY hardcoded em app.py:7)
git show 'upstream/main:code-smells-project/app.py' | sed -n '1,10p'

# o diff completo de um projeto
git diff upstream/main HEAD -- code-smells-project/
```

A linha-base é o commit `6d1ce62` de `upstream/main`. Todos os `arquivo:linha` dos relatórios
foram conferidos contra ela — ver [Verificação dos findings](#verificação-dos-findings-contra-a-linha-base).

---

## A) Análise Manual

Análise dos 3 projetos contra o código da linha-base (`upstream/main`). Os relatórios em
`reports/` trazem o conjunto completo; abaixo estão os problemas de maior impacto arquitetural.

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| Severidade | Problema (`arquivo:linha` no original) | Por que é relevante |
|---|---|---|
| CRITICAL | SQL Injection por concatenação em toda a camada de dados — `models.py:28, 47-50, 109-111, 148-151, 289-297` | Permite ler/alterar/destruir o banco e burlar o login com `' OR '1'='1` |
| CRITICAL | `POST /admin/query` executa SQL arbitrário sem auth — `app.py:59-78` | Comprometimento total do banco por qualquer requisitante |
| CRITICAL | Senhas em texto puro, comparadas em SQL e **devolvidas** nas respostas — `models.py:83, 99, 127-129`; `database.py:76-78` | Vazamento direto de credenciais de todos os usuários |
| CRITICAL | `SECRET_KEY` hardcoded e exposta no `/health` + `DEBUG=True` — `app.py:7, 8`; `controllers.py:285-289` | Segredo público e RCE via console do debugger do Werkzeug |
| HIGH | `app.py` roteia **e** executa SQL (god file); sem camadas reais — `app.py:11-30, 47-78` | Impossível testar ou isolar qualquer comportamento |
| HIGH | Criação de pedido sem transação — `models.py:133-169` | Falha no meio deixa pedido e estoque inconsistentes, sem rollback |
| MEDIUM | N+1 ao listar pedidos: uma query de itens por pedido — `models.py:171-201, 203-233` | Custo cresce linearmente com o número de pedidos |
| MEDIUM | Validação frágil: `if preco_min:` descarta o valor `0` — `controllers.py:118` | Filtro de preço mínimo `0` é silenciosamente ignorado |
| MEDIUM | Exceção interna devolvida ao cliente em 14 handlers — `controllers.py:12, 22, 62, …, 292` | Vaza mensagem do banco e da stack para quem chama a API |
| LOW | Magic numbers das faixas de desconto — `models.py:257-262` | Regra de negócio ilegível e duplicada em condicionais |
| LOW | Parâmetro `id` sombreia o builtin — `controllers.py:14, 64, 98, 136`; `models.py:24, 54, 65, 89` | Confunde leitura e impede uso de `id()` no escopo |
| LOW | Concatenação de strings onde caberia f-string — `controllers.py:8`; `models.py:48-49` | Ruído e risco de erro de tipo em `str()` manual |

### Projeto 2 — `ecommerce-api-legacy` (Node/Express, LMS + checkout)

| Severidade | Problema (`arquivo:linha` no original) | Por que é relevante |
|---|---|---|
| CRITICAL | Segredos hardcoded: `pk_live_1234567890abcdef`, senha do banco — `utils.js:2-5` | Chave de produção e credencial versionadas no repositório |
| CRITICAL | Número do cartão **e** chave do gateway escritos em log — `AppManager.js:45` | Violação de PCI-DSS e vazamento de segredo em qualquer coletor de logs |
| CRITICAL | Hashing caseiro (`badCrypto`) e senha em texto puro no seed — `utils.js:17-23`; `AppManager.js:12, 18` | Senhas trivialmente reversíveis |
| CRITICAL | God Class `AppManager`: conexão, schema, rotas, negócio e pagamento — `AppManager.js:4-139` | Acoplamento total; nada é testável em isolamento |
| CRITICAL | `/api/admin/financial-report` e `DELETE /api/users/:id` sem auth — `AppManager.js:80, 131` | Broken access control: receita e exclusão de usuários abertas |
| HIGH | Autorização de pagamento fictícia: `cc.startsWith("4")` — `AppManager.js:46` | Qualquer número começando com 4 "paga"; matrícula concedida de graça |
| MEDIUM | N+1 no relatório financeiro: query por curso, por matrícula e por usuário — `AppManager.js:83-127` | Relatório degrada proporcionalmente ao catálogo |
| MEDIUM | Coordenação assíncrona manual com contadores — `AppManager.js:86-122` | Callback hell; erro em qualquer ramo deixa a resposta pendurada |
| MEDIUM | Validação incompleta no checkout: senha (`p`) nunca é checada — `AppManager.js:35` | Cria usuário sem senha utilizável |
| LOW | Nomes crípticos de variável (`u`, `e`, `p`, `cid`, `cc`) — `AppManager.js:29-33` | Ilegível justamente no fluxo de pagamento |
| LOW | Código morto exportado como se fosse usado (`totalRevenue`) — `utils.js:10, 25` | Sugere estado global compartilhado que ninguém consome |
| LOW | Magic numbers e loop inútil de 10 000 iterações — `utils.js:6, 19, 22` | Custo sem propósito no caminho de hashing |

### Projeto 3 — `task-manager-api` (Python/Flask + SQLAlchemy, Task Manager)

| Severidade | Problema (`arquivo:linha` no original) | Por que é relevante |
|---|---|---|
| CRITICAL | Senha em **MD5 sem salt** — `models/user.py:29, 32` | Hash quebrado; rainbow tables resolvem em segundos |
| CRITICAL | Hash da senha **devolvido** nas respostas — `models/user.py:21`; `user_routes.py:33, 85-86, 129, 209` | Exposição do material de credencial em 4 endpoints |
| CRITICAL | `SECRET_KEY` e credenciais SMTP hardcoded — `app.py:13`; `services/notification_service.py:9-10` | Segredos versionados |
| CRITICAL | `debug=True` com bind em `0.0.0.0` — `app.py:34` | Console do debugger exposto na rede |
| HIGH | Sem camada controller/service — as rotas fazem tudo — `task_routes.py:11-299`; `user_routes.py:10-211`; `report_routes.py:12-223` | Viola MVC apesar da organização parcial de diretórios |
| HIGH | Token de login forjável: `'fake-jwt-token-' + str(user.id)` — `user_routes.py:210` | Impersonação trivial de qualquer usuário |
| HIGH | `DELETE /categories/:id` deixa tasks órfãs — `report_routes.py:211-223` | Quebra de integridade referencial |
| MEDIUM | N+1 em tasks, relatório e categorias — `task_routes.py:41-57`; `report_routes.py:55-68, 161-164` | Custo linear no número de registros |
| MEDIUM | 12 `count()` redundantes num único relatório — `report_routes.py:15-28` | Doze varreduras onde uma agregação resolveria |
| MEDIUM | APIs deprecated: `Model.query.get` (16×) e `datetime.utcnow()` (22×) | Removidas no SQLAlchemy 2.0 / deprecadas no Python 3.12 |
| MEDIUM | Regra de "atrasado" duplicada 6× enquanto `Task.is_overdue()` existe e nunca é chamado — `models/task.py:50-60` | Seis lugares para corrigir a mesma regra |
| LOW | `utils/helpers.py` é código morto integral (funções e 7 constantes com 0 usos) | Arquivo inteiro mantido sem consumidor |
| LOW | Magic numbers e strings soltos nas rotas — `task_routes.py:96-100, 110, 113` | Status e prioridades repetidos como literais |
| LOW | `type(x) == list` e returns booleanos verbosos — `task_routes.py:141, 210`; `utils/helpers.py:103` | Antipadrão de comparação de tipo |

---

## B) Construção da Skill

**Estrutura.** O `SKILL.md` é o **prompt orquestrador**; os 5 arquivos de referência carregam o
**conhecimento de domínio** (progressive disclosure — cada um é lido no início da fase
correspondente):

| Arquivo | Área de conhecimento |
|---|---|
| `SKILL.md` | Orquestra as 3 fases e os princípios inegociáveis |
| `references/01-project-analysis.md` | Heurísticas de detecção (linguagem, framework, DB, arquitetura, endpoints) |
| `references/02-antipattern-catalog.md` | 22 anti-patterns + seção de APIs deprecated (severidade + sinais) |
| `references/03-audit-report-template.md` | Formato padronizado do relatório |
| `references/04-mvc-architecture-guidelines.md` | Camadas MVC + mapa de tradução Python↔Node |
| `references/05-refactoring-playbook.md` | 15 transformações antes/depois (Python e Node) |

**Anti-patterns incluídos e por quê.** O catálogo (CRITICAL→LOW) foi derivado diretamente da
análise manual: cada problema real virou um **sinal de detecção acionável** (ex.: "query SQL por
concatenação", "`card.startsWith` como autorização", "`Model.query.get`"). Cobre segredos
hardcoded, SQL injection, God Class, hashing fraco, exposição de dados, debug/RCE, broken access
control, lógica no controller, ausência de DI, estado global, falta de transação, token forjável,
N+1, validação ausente, duplicação, CORS aberto, sem paginação, logging por `print`, magic
numbers, dead code — **+ detecção de APIs deprecated** com o equivalente moderno.

O critério para incluir um anti-pattern foi **ser detectável por um sinal objetivo**. "Código ruim"
não entra; "`BEGIN` emitido fora do `try`, sem `ROLLBACK` no caminho de erro" entra, porque um
agente consegue procurar exatamente isso.

**Como garanti o agnosticismo.** (1) Detecção por **arquivo-marcador** (`requirements.txt` →
Python, `package.json` → Node); (2) **mapa de tradução de camadas** nas guidelines (Blueprint↔Router,
`@app.errorhandler`↔middleware, `werkzeug`↔`bcrypt`); (3) playbook com exemplos **nas duas stacks**;
(4) a skill não codifica nomes de arquivo de nenhum projeto. **Teste decisivo:** a mesma pasta
`refactor-arch/` foi copiada sem edição para os 3 projetos — as três cópias são byte-idênticas
(conferido por MD5), e é a mesma skill que produziu os 3 relatórios.

**Desafios e soluções.**

1. *Preservar o contrato de endpoints* → a Fase 1 monta um inventário método+path que serve de base
   ao smoke test da Fase 3. Conferido contra a linha-base: **19→19** (P1), **3→3** (P2) e
   **22→22** (P3) endpoints, sem nenhum path ou método alterado.
2. *Timezone no SQLAlchemy/SQLite* (mistura aware/naive ao trocar `datetime.utcnow`) → helper
   `utcnow()` que retorna UTC **naive**, removendo a deprecação sem quebrar comparações.
3. *Portabilidade do hashing* → `werkzeug` usa `scrypt` por default, ausente em builds de Python sem
   OpenSSL com suporte a scrypt (reproduzido no Python 3.9 do macOS, LibreSSL 2.8.3; em P1 derrubava
   o boot inteiro, pois o seed roda no `init_db()`). Fixado `method="pbkdf2:sha256"` e documentado
   no Playbook P4.
4. *Endpoints perigosos* → em vez de removê-los, foram protegidos por guard, mantendo "todos os
   endpoints respondem": **admin-guard** (Playbook P12) e **login-guard** (P13).
5. *Verificação de negócio fake movida, mas não corrigida* → no P2, a Fase 3 original isolou
   `cc.startsWith("4")` numa classe `PaymentGateway` sem trocar a heurística. Daí o anti-pattern
   **H6** (fake business verification, distinto de H5 — identidade ≠ legitimidade da operação) e o
   **Playbook P14**: verificação estrutural real (checksum de Luhn) + casos de teste determinísticos
   para os caminhos de erro, na convenção de gateways reais em sandbox.
6. *A lição mais custosa: refatorar a estrutura não corrige a autorização.* Uma auditoria por
   agentes independentes mostrou que os três projetos saíram da Fase 3 com a camada de dados bem
   feita (SQL parametrizado, hashing correto, transações) e a camada de **autorização ausente**. No
   P3 o guard gravava `g.current_user_id` e **nenhum service lia esse valor** — "estar logado"
   equivalia a acesso total, e uma usuária comum conseguia rebaixar o admin. No P1 não havia
   mecanismo de sessão algum, então nem era possível proteger as rotas. Isso gerou o **Playbook
   P15 — Autorização por dono (fim do IDOR)** e novos sinais no anti-pattern `C7`, todos
   detectáveis por grep: contexto de usuário gravado e nunca lido, helper `is_admin()` definido e
   nunca chamado, `role` aceito do corpo da requisição, listagem sem cláusula de dono, troca de
   senha sem exigir a senha atual. Detalhes e provas nos adendos dos 3 relatórios.
7. *Default de segredo é pior do que segredo ausente.* A primeira rodada trocou segredos hardcoded
   por `os.environ.get("SECRET_KEY", "dev-secret-change-in-production")` — o que parece correto e
   não é: a constante continua versionada e, no P3, era exatamente a chave que assina a sessão, de
   modo que qualquer pessoa com acesso ao repositório forjava a sessão de qualquer usuário
   (demonstrado em runtime). Hoje os três projetos **falham na inicialização** sem os segredos, com
   `FLASK_ENV=development` gerando valor efêmero em memória.

---

## C) Resultados

### Findings por severidade

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 8 | 6 | 8 | 3 | **25** |
| 2 — ecommerce-api-legacy | 6 | 6 | 5 | 4 | **21** |
| 3 — task-manager-api | 5 | 5 | 9 | 4 | **23** |

### Verificação dos findings contra a linha-base

Os **69 findings** foram reconferidos, um a um, contra o código original em `upstream/main`
(cada `File: arquivo:linha` foi aberto e lido no commit da linha-base):

| Projeto | Confirmados | Linha imprecisa | Não localizados | Sem linha exata |
|---|---|---|---|---|
| 1 | 24 / 25 | 0 | 0 | 1 |
| 2 | 21 / 21 | 0 | 0 | 0 |
| 3 | 21 / 23 | 0 | 0 | 2 |

Nenhum finding é inventado e nenhuma linha estava errada. As métricas da Fase 1 também batem
exatamente: P1 = 4 arquivos / 780 linhas (88+292+314+86), P2 = 3 arquivos / 180 linhas
(14+141+25), P3 = 15 arquivos / 1158 linhas físicas (969 SLOC). As referências que estavam
genéricas ("todas as funções", "maioria") foram substituídas por linhas concretas, e 3 imprecisões
de detalhe foram corrigidas nos relatórios — ver os adendos de 2026-09-02.

### Antes → Depois (estrutura)

- **P1:** monólito plano (`app.py`, `controllers.py`, `models.py`, `database.py`, 780 linhas) →
  `src/` com `config / models(repositories) / services / controllers / views / middlewares` +
  composition root.
- **P2:** God Class `AppManager` + `utils.js` (180 linhas) → `src/` com
  `config / models / services / controllers / routes / middlewares` + bootstrap async com injeção
  de dependência.
- **P3:** parcialmente em camadas, sem controller/service → adicionadas as camadas `controllers/` e
  `services/`, `category_routes.py` (as rotas de categoria moravam dentro de `report_routes.py`) e
  `middlewares/`; a lógica saiu das rotas.

### Validação — boot e endpoints

Cada projeto foi levantado de fato e exercitado com requisições reais.

| Projeto | Boot | Endpoints originais | Respostas 5xx | Tracebacks |
|---|---|---|---|---|
| 1 | ✅ limpo | **19/19** respondem | 0 | 0 |
| 2 | ✅ limpo | **3/3** respondem | 0 | 0 |
| 3 | ✅ limpo | **22/22** respondem | 0 | 0 |

**P1 — log de boot e matriz de autorização** (`porta 5401`):

```
SERVIDOR INICIADO
Rodando em http://localhost:5401
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5401

ENDPOINT                                 S/TOKEN  CLIENTE  ADMIN
GET /                                    200      200      200
GET /health                              200      200      200
POST /login                              200      -        -
GET /produtos                            200      200      200
GET /produtos/busca                      200      -        -
GET /produtos/1                          200      -        -
POST /produtos                           401      403      201
PUT /produtos/1 (payload completo)        401      403      200
GET /usuarios                            401      403      200
GET /usuarios/2 (próprio usuário)         401      200      200
GET /usuarios/3 (outro usuário)           401      403      200
POST /usuarios                           201      -        -
POST /pedidos                            401      201      201
GET /pedidos                             401      403      200
GET /pedidos/usuario/2 (próprio)          401      200      200
GET /pedidos/usuario/3 (outro)            401      403      200
PUT /pedidos/1/status                    401      403      200
GET /relatorios/vendas                   401      403      200
POST /admin/query                        401      403      200
POST /admin/query sem X-Admin-Token       -        -        401
DELETE /produtos/<id>                    401      403      200

respostas 5xx: 0 | tracebacks: 0
```

**P1 — hardening do `/admin/query`** (executava SQL arbitrário; hoje aceita uma única instrução
`SELECT` sobre allowlist):

```
RECUSADOS (HTTP 400)
  UPDATE produtos SET preco = 0                      Apenas consultas SELECT são permitidas
  DROP TABLE usuarios                                Apenas consultas SELECT são permitidas
  PRAGMA database_list                               Apenas consultas SELECT são permitidas
  SELECT id FROM usuarios; SELECT id FROM produtos   Apenas uma instrução por requisição
  SELECT senha FROM usuarios                         A coluna `senha` não pode ser consultada
  SELECT * FROM sqlite_master                        Tabela não permitida: sqlite_master
  SELECT * FROM usuarios -- comentario               Comentários SQL não são permitidos
  INSERT INTO usuarios (nome) VALUES ('x')           Apenas consultas SELECT são permitidas
  ATTACH DATABASE '/tmp/x.db' AS x                   Apenas consultas SELECT são permitidas

ACEITOS (HTTP 200)
  SELECT id, nome, preco FROM produtos
  SELECT COUNT(*) AS total FROM pedidos
  SELECT p.id, u.nome FROM pedidos p JOIN usuarios u ON u.id = p.usuario_id
  SELECT * FROM usuarios          -> 0 ocorrências da chave "senha" no payload
```

**P2 — concorrência no checkout** (a fila de transações corrigiu 9 de 10 requisições que falhavam):

```
antes (sem fila): 9x HTTP 500 "SQLITE_ERROR: cannot start a transaction within a transaction"
depois:
req 1..10 -> HTTP 200 {"msg":"Sucesso","enrollment_id":5..14}
contagem: 10x HTTP 200 — zero 500
grep -ci 'cannot start a transaction' server.log -> 0
integridade: 12 alunos, 12 pagamentos, nenhuma matrícula sem pagamento

compensação de cobrança (falha de persistência forçada após aprovação):
  cliente recebeu: HTTP 500 {"erro":"Erro interno no servidor"}
  log do servidor: [checkout] persistência falhou após cobrança aprovada, estornando cobrança
                   [checkout] cobrança estornada com sucesso { status: 'REFUNDED' }
  (o texto SQLITE_ERROR aparece apenas no log, nunca na resposta)
```

**P3 — os oito ataques que a auditoria demonstrou como bem-sucedidos** (executados com a conta
`maria@email.com`, `role=user`):

```
 * Running on http://127.0.0.1:5301   (Debug mode: off)

PUT /users/1 (renomear/rebaixar o admin João)             403
DELETE /tasks/1 (task do João)                            403
GET /reports/summary (produtividade de todos)             403
GET /users (e-mail de todos)                              403
GET /users/1 (dados do João)                              403
GET /reports/user/1 (relatório do João)                   403
GET /tasks/1 (task do João)                               403
PUT /tasks/1 (task do João)                               403
  -> admin João segue intacto: nome=João Silva role=admin

token forjado com a constante que estava versionada:
  GET /users  -> 401   (antes: 200 com os dados de todos os usuários)
  GET /tasks  -> 401

escopo por dono:  Maria vê 3 tasks (user_ids=[2]) | admin vê 10 (user_ids=[1,2,3])
                  stats da Maria: total=3 | stats do admin: total=10
                  GET /tasks/search?user_id=1 pela Maria -> 403

mass assignment:  cadastro anônimo pedindo role=admin -> HTTP 201, role gravado: 'user'
                  usuário comum tentando se promover   -> 403
                  admin promovendo via PUT /users/2    -> 200, role: 'manager'

troca de senha:   sem current_password         -> 403
                  com current_password errada  -> 403
                  com current_password correta -> 200

validações que antes devolviam 500:
  PUT /users/2 {"password":null}        400
  PUT /users/2 {"name":null}            400
  PUT /users/2 {"active":"talvez"}      400
  PUT /categories/1 {"name":null}       400

varredura dos 22 endpoints com token de admin: 22/22 em 2xx | 5xx: 0 | tracebacks: 0
```

**Segredos obrigatórios nos 3 projetos** — nenhum default versionado sobrevive:

```
$ env -u SECRET_KEY -u ADMIN_TOKEN python app.py          # P1
ERRO DE CONFIGURAÇÃO: A variável de ambiente obrigatória SECRET_KEY não está definida. [...]
Para conveniência local, use FLASK_ENV=development para gerar um valor aleatório efêmero.

$ env -u SECRET_KEY python app.py                          # P3
RuntimeError: SECRET_KEY não está definida no ambiente. [...]

$ env -u ADMIN_TOKEN -u PAYMENT_GATEWAY_KEY node src/app.js  # P2
[config] Configuração obrigatória ausente: ADMIN_TOKEN, PAYMENT_GATEWAY_KEY. [...]
Não existe valor default para segredos.
exit=1
```

**Provas de segurança adicionais em runtime:** SQL Injection no login bloqueada (P1: `' OR '1'='1`
→ 401; busca com payload SQLi → 0 resultados); nenhum log com cartão ou chave de gateway (P2);
nenhuma resposta com `password`/`senha`/`secret` nos 3 projetos; `POST /pedidos` grava o
`usuario_id` do token e ignora o do corpo (P1: pediu 3, persistiu 2); cadastro com e-mail duplicado
→ 409 (P1, antes 201); cartão Luhn-válido → 200 e Luhn-inválido → 400 com o **mesmo prefixo de
bandeira** (P2), provando que a decisão não depende mais da bandeira.

### Checklist de Validação — Projeto 1 (`code-smells-project`)

```
Fase 1 — Análise
[x] Linguagem detectada corretamente              Python
[x] Framework detectado corretamente              Flask 3.1.1 (confere com requirements.txt)
[x] Domínio descrito corretamente                 API de E-commerce (produtos/usuários/pedidos)
[x] Número de arquivos condiz                     4 arquivos / 780 linhas (conferido na linha-base)

Fase 2 — Auditoria
[x] Relatório segue o template das referências
[x] Cada finding tem arquivo e linhas exatos      25/25 com File:; 24 confirmados na linha-base
[x] Findings ordenados por severidade             CRITICAL → HIGH → MEDIUM → LOW
[x] Mínimo de 5 findings                          25
[x] Pelo menos 1 CRITICAL ou HIGH                 8 CRITICAL + 6 HIGH
[x] Detecção de APIs deprecated incluída          SQL cru sem camada de persistência
[x] Pausa pedindo confirmação antes da Fase 3

Fase 3 — Refatoração
[x] Estrutura de diretórios segue padrão MVC      src/{config,models,services,controllers,views,middlewares}
[x] Config extraída, sem segredos hardcoded       falha no boot sem SECRET_KEY/ADMIN_TOKEN
[x] Models/repositories abstraem os dados         4 repositories, queries 100% parametrizadas
[x] Views/Routes separadas                        src/views/routes.py só mapeia path → controller
[x] Controllers concentram o fluxo
[x] Error handling centralizado                   src/middlewares/error_handler.py + src/errors.py
[x] Entry point claro                             app.py → src/app.py::create_app
[x] Aplicação inicia sem erros                    log de boot limpo
[x] Endpoints originais respondem                 19/19, 0 respostas 5xx
```

### Checklist de Validação — Projeto 2 (`ecommerce-api-legacy`)

```
Fase 1 — Análise
[x] Linguagem detectada corretamente              JavaScript (Node.js)
[x] Framework detectado corretamente              Express ^4.18.2 (confere com package.json)
[x] Domínio descrito corretamente                 LMS com fluxo de checkout
[x] Número de arquivos condiz                     3 arquivos / 180 linhas (conferido na linha-base)

Fase 2 — Auditoria
[x] Relatório segue o template das referências
[x] Cada finding tem arquivo e linhas exatos      21/21, todos confirmados na linha-base
[x] Findings ordenados por severidade
[x] Mínimo de 5 findings                          21
[x] Pelo menos 1 CRITICAL ou HIGH                 6 CRITICAL + 6 HIGH
[x] Detecção de APIs deprecated incluída          pirâmide de callbacks do sqlite3
[x] Pausa pedindo confirmação antes da Fase 3

Fase 3 — Refatoração
[x] Estrutura de diretórios segue padrão MVC      src/{config,models,services,controllers,routes,middlewares}
[x] Config extraída, sem segredos hardcoded       exit(1) sem ADMIN_TOKEN/PAYMENT_GATEWAY_KEY
[x] Models/repositories abstraem os dados         6 repositories, queries 100% parametrizadas
[x] Views/Routes separadas                        3 routers, apenas verbo + guard
[x] Controllers concentram o fluxo                controllers finos sob asyncHandler
[x] Error handling centralizado                   errorHandler + hierarquia em src/errors.js
[x] Entry point claro                             src/app.js com createApp() e require.main guard
[x] Aplicação inicia sem erros                    log de boot limpo, sem warnings
[x] Endpoints originais respondem                 3/3, incluindo 10 checkouts concorrentes
```

### Checklist de Validação — Projeto 3 (`task-manager-api`)

```
Fase 1 — Análise
[x] Linguagem detectada corretamente              Python
[x] Framework detectado corretamente              Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
[x] Domínio descrito corretamente                 Task Manager (tasks/users/categories/reports)
[x] Número de arquivos condiz                     15 arquivos .py / 1158 linhas (969 SLOC)

Fase 2 — Auditoria
[x] Relatório segue o template das referências
[x] Cada finding tem arquivo e linhas exatos      23/23 com File:; 21 confirmados na linha-base
[x] Findings ordenados por severidade
[x] Mínimo de 5 findings                          23
[x] Pelo menos 1 CRITICAL ou HIGH                 5 CRITICAL + 5 HIGH
[x] Detecção de APIs deprecated incluída          Model.query.get (16x) e datetime.utcnow (22x)
[x] Pausa pedindo confirmação antes da Fase 3

Fase 3 — Refatoração
[x] Estrutura de diretórios segue padrão MVC      config/models/routes/controllers/services/middlewares
[x] Config extraída, sem segredos hardcoded       falha no boot sem SECRET_KEY
[x] Models abstraem os dados                      to_dict() nunca expõe o hash da senha
[x] Views/Routes separadas                        4 blueprints, apenas add_url_rule
[x] Controllers concentram o fluxo                services sem nenhum import de flask
[x] Error handling centralizado                   error_handler.py com rollback + errors.py
[x] Entry point claro                             app-factory create_app()
[x] Aplicação inicia sem erros                    boot sem warnings de deprecação
[x] Endpoints originais respondem                 22/22, 0 respostas 5xx
```

### Ganhos de performance medidos

O N+1 foi eliminado de fato, não apenas reescrito. No P3 as queries foram contadas por
instrumentação do SQLAlchemy (`before_cursor_execute`), comparando o seed com um cenário 30×
maior — as contagens **não crescem** com o volume:

| Endpoint | 10 tasks | 300 tasks / 50 users |
|---|---|---|
| `GET /tasks` | 1 query | 1 query |
| `GET /users` | 2 queries | 2 queries |
| `GET /categories` | 2 queries | 2 queries |
| `GET /reports/summary` | 9 queries | 9 queries |
| `GET /reports/user/1` | 2 queries | 2 queries |
| `GET /tasks/stats` | 3 queries | 3 queries |

No P2, o relatório financeiro que fazia uma query por curso, por matrícula e por usuário passou a
ser um único JOIN.

### Limitações conhecidas

Esta seção existe porque "zero anti-patterns remanescentes" seria uma afirmação falsa, e um
avaliador confere isso com um `grep`. O que **ficou fora de escopo**, por projeto:

- **P1:** paginação nas listagens; `CORS_ORIGINS` com valor efetivo `*`; `print()` no boot;
  comparação do token de admin sem `hmac.compare_digest`; credenciais de exemplo do seed
  (`admin@loja.com` / `admin123`) criadas automaticamente quando o banco está vazio.
- **P2:** `helmet` e rate limiting ausentes; checkout sem idempotência (retry gera nova cobrança);
  matrícula em conta de e-mail existente sem prova de posse; 13 vulnerabilidades transitivas do
  `npm audit` em dependências do `sqlite3`.
- **P3:** paginação; `CORS(app)` irrestrito; `NotificationService` como código morto;
  `MIN_PASSWORD_LENGTH = 4`; login sem rate limiting.

Nenhum desses itens afeta os critérios de aceite do desafio, e todos estão registrados como
findings nos relatórios — a diferença é que agora está explícito o que foi corrigido e o que não.

### Observações por stack

A skill se comportou de forma consistente: nos **monólitos** (P1/P2) criou todas as camadas do
zero; no projeto **parcialmente organizado** (P3) **não recriou** o que já estava correto —
introduziu apenas as camadas faltantes (controller/service), reaproveitou `Task.is_overdue()` e as
constantes de `utils/helpers.py` que estavam ociosas, e moveu as categorias para um blueprint
próprio. Persistência foi mantida por stack (sqlite3 nativo parametrizado em P1/P2; SQLAlchemy 2.0
em P3), provando adaptação ao contexto.

---

## D) Como Executar

**Pré-requisitos:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
instalado · Python 3.9+ (validado no 3.9.6 do macOS) · Node.js 20+.

**Invocar a skill** (já copiada para os 3 projetos):

```bash
cd code-smells-project     && claude "/refactor-arch"   # Projeto 1
cd ../ecommerce-api-legacy && claude "/refactor-arch"   # Projeto 2
cd ../task-manager-api     && claude "/refactor-arch"   # Projeto 3
```

A Fase 2 **pausa** e imprime `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`.
Nenhum arquivo é criado, alterado ou apagado antes do `y`.

**Variáveis de ambiente são obrigatórias.** Os três projetos falham na inicialização, com mensagem
explícita, se os segredos não vierem do ambiente — não existe default versionado. Para desenvolvimento
local, os projetos Python aceitam `FLASK_ENV=development`, que gera valores efêmeros em memória
(mudam a cada boot e invalidam os tokens anteriores).

```bash
# Projeto 1 — code-smells-project (Flask)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
export ADMIN_TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
python app.py                                  # http://localhost:5000

# Projeto 3 — task-manager-api (Flask + SQLAlchemy)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
python seed.py                                 # popula 3 usuários, 4 categorias, 10 tasks
python app.py                                  # http://localhost:5000

# Projeto 2 — ecommerce-api-legacy (Express)
npm install
export ADMIN_TOKEN="$(openssl rand -hex 32)"
export PAYMENT_GATEWAY_KEY="sk_test_sandbox"
npm start                                      # http://localhost:3000
```

**Como validar que a refatoração funciona.**

```bash
# 1. A app sobe sem erros — e NÃO sobe sem os segredos (comportamento esperado)
env -u SECRET_KEY python app.py      # deve abortar com ERRO DE CONFIGURAÇÃO

# 2. Endpoints públicos respondem sem credencial
curl -s localhost:5000/health
curl -s localhost:5000/produtos          # P1: catálogo é público

# 3. Endpoints protegidos exigem sessão — obtenha o token no login
TOKEN=$(curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@loja.com","senha":"admin123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['dados']['token'])")   # P1
curl -s localhost:5000/usuarios -H "Authorization: Bearer $TOKEN"

# 4. Sem token deve dar 401; com token de usuário comum em rota de admin, 403
curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/usuarios          # 401
curl -s -o /dev/null -w '%{http_code}\n' localhost:5000/relatorios/vendas # 401

# 5. /admin/* exige o header E sessão de admin
curl -s -X POST localhost:5000/admin/query -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"sql":"SELECT id, nome FROM produtos"}'
# e deve RECUSAR escrita:
curl -s -X POST localhost:5000/admin/query -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"sql":"UPDATE produtos SET preco = 0"}'                            # 400

# 6. Nenhum segredo ou hash de senha nas respostas
curl -s localhost:5000/usuarios -H "Authorization: Bearer $TOKEN" | grep -c senha   # 0
curl -s localhost:5000/health | grep -cE 'secret|db_path'                           # 0
```

No **Projeto 2**, use o `api.http` (o token vem de `{{$processEnv ADMIN_TOKEN}}`, não versionado).
No **Projeto 3**, o login é `POST /login` com `{"email":"joao@email.com","password":"1234"}` (admin
do seed) e o token vai em `Authorization: Bearer <token>`.

**Para comparar com o código original**, use os comandos de
[Como ver o diff antes → depois](#como-ver-o-diff-antes--depois).

---
# Enunciado do Desafio (original)

# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.