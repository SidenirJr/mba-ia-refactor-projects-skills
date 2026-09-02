```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (versão não fixada no repositório)
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x)
Dependencies:  flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0
               (marshmallow, requests e python-dotenv declarados mas NÃO usados)
Domain:        Task Manager API — CRUD de tasks, users (com login), categories + relatórios
Architecture:  Parcialmente em camadas (models/routes/services/utils) mas SEM controller/service
               real: rotas acumulam roteamento + lógica de negócio + acesso a dados
Source files:  15 .py files analyzed (1158 linhas físicas, 969 SLOC — o código original
               não tem nenhuma linha de comentário, logo não-vazias = SLOC)
DB tables:     users, tasks, categories (SQLite, sqlite:///tasks.db)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   15 analyzed | 1158 linhas físicas (969 SLOC)

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 9 | LOW: 4

## Findings

### [CRITICAL] SECRET_KEY hardcoded
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` no código.
Impact: Segredo versionado.
Recommendation: Config por variável de ambiente. Playbook P1.

### [CRITICAL] Credenciais SMTP hardcoded
File: services/notification_service.py:9-10
Description: `email_user = 'taskmanager@gmail.com'` / `email_password = 'senha123'` em texto puro.
Impact: Credenciais de e-mail expostas no repositório.
Recommendation: Mover para variáveis de ambiente. Playbook P1.

### [CRITICAL] Hash de senha com MD5 sem salt
File: models/user.py:29, 32
Description: `hashlib.md5(pwd.encode()).hexdigest()` — algoritmo quebrado e sem salt.
Impact: Senhas vulneráveis a quebra/rainbow tables.
Recommendation: `werkzeug.security` (generate/check_password_hash) — bcrypt/scrypt. Playbook P4.

### [CRITICAL] Hash de senha vazado nas respostas
File: models/user.py:21 (to_dict inclui 'password')
Description: Exposto por `GET /users/<id>` (user_routes.py:33), `POST /users` (:85-86), `PUT` (:129) e `/login` (:209).
Impact: Hash de todos os usuários devolvido à API.
Recommendation: Remover `password` do `to_dict`. Playbook P5.

### [CRITICAL] Debug mode ligado em todas as interfaces
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)`.
Impact: Debugger interativo do Werkzeug → execução remota de código.
Recommendation: DEBUG via env, default desligado. Playbook P1.

### [HIGH] Sem camada de controller/service — rotas fazem tudo
File: task_routes.py:11-299; user_routes.py:10-211; report_routes.py:12-223 (todas as rotas
dos três blueprints, da primeira à última linha de cada arquivo)
Description: As rotas roteiam, validam, aplicam regra de negócio E acessam o banco diretamente.
Impact: Viola MVC/SRP; nada é reutilizável ou testável isoladamente.
Recommendation: Introduzir controllers finos + camada de services. Playbook P3/P6.

### [HIGH] Lógica de negócio nas rotas
File: task_routes.py:30-57, 273-299; report_routes.py:13-101
Description: Cálculo de overdue, agregações e montagem de relatório inline nas rotas.
Impact: Difícil de testar e manter.
Recommendation: Mover para services. Playbook P6.

### [HIGH] Autenticação ausente e token forjável
File: user_routes.py:210
Description: Login retorna `'fake-jwt-token-' + str(user.id)` — previsível, sem assinatura/expiração; nenhum endpoint exige auth.
Impact: Impersonação trivial.
Recommendation: Token assinado (itsdangerous/JWT). Playbook P12.

### [HIGH] Delete de categoria deixa tasks órfãs
File: report_routes.py:211-223
Description: `delete_category` apaga a categoria mas deixa tasks apontando para `category_id` inexistente (sem cascade), diferente de `delete_user` que limpa tasks.
Impact: Violação de integridade referencial, tratada de forma inconsistente.
Recommendation: Limpar/!setar nulo nas tasks em transação. Playbook P8.

### [HIGH] Categoria pertence ao blueprint errado
File: report_routes.py:157-223
Description: CRUD de categorias hospedado em `report_routes` (sob "reports"), sem `category_routes.py`.
Impact: Organização assimétrica e confusa.
Recommendation: Mover para um blueprint/controller próprio, preservando os paths `/categories`. Playbook P3.

### [MEDIUM] Queries N+1
File: task_routes.py:41-57; report_routes.py:55-68, 160-164; user_routes.py:22
Description: `User.query.get`/`Category.query.get` por task no loop; `Task.query.filter_by` por usuário/categoria no loop; `len(u.tasks)` por usuário.
Impact: Explosão de consultas.
Recommendation: Eager loading (joinedload) e queries agregadas. Playbook P9.

### [MEDIUM] Counts redundantes
File: report_routes.py:15-28; task_routes.py:275-281
Description: 12 `count()` separados só na faixa 15-28 (14 na função `summary_report` inteira,
somando `report_routes.py:46` e `48-51`) e 5 counts + reload de todas as tasks no stats.
Impact: Várias idas ao banco evitáveis.
Recommendation: Agregação única com GROUP BY. Playbook P9.

### [MEDIUM] Lógica de overdue duplicada 6×
File: task_routes.py:30-39, 71-80, 284-287; user_routes.py:171-180; report_routes.py:34-37, 132-135
Description: Mesmo bloco aninhado repetido, enquanto `Task.is_overdue()` (models/task.py:50-60) existe e é ignorado.
Impact: Manutenção multiplicada.
Recommendation: Reutilizar `Task.is_overdue()`. Playbook P6.

### [MEDIUM] Serialização e validação duplicadas
File: task_routes.py:17-28 vs models/task.py:23-36; task_routes.py:96-114 vs 166-184; user_routes.py:61,106 vs utils/helpers.py:21
Description: Dict manual duplica `to_dict`; validação de título/status/prioridade triplicada; regex de email repetida (helper existe e é ignorado).
Impact: Inconsistência e retrabalho.
Recommendation: Centralizar em service + reutilizar helpers/constantes existentes. Playbook P6/P10.

### [MEDIUM] Validação ausente / casts inseguros
File: task_routes.py:113, 261, 264; report_routes.py:196
Description: `priority < 1` sem `int()`; `int(priority)`/`int(user_id)` sem guard; `update_category` não checa `get_json()` None.
Impact: 500 com entradas inválidas.
Recommendation: Validação centralizada e coerção segura. Playbook P10.

### [MEDIUM] except amplo/silencioso retornando 500 genérico
File: task_routes.py:62,137,204,236; user_routes.py:130,149; report_routes.py:186,207,221
Description: `except:`/`except Exception` engolindo erros.
Impact: Erros mascarados e difíceis de diagnosticar.
Recommendation: Error handler central. Playbook P10.

### [MEDIUM] Sem paginação
File: task_routes.py:14, 266; user_routes.py:12; report_routes.py:30, 53, 109, 159
Description: Listagens retornam a tabela inteira (o próprio seed registra isso como problema conhecido).
Impact: Não escala.
Recommendation: limit/offset.

### [MEDIUM] API deprecated: Query.get e datetime.utcnow
File: task_routes.py:42,51,67,...; user_routes.py:29,94,...; report_routes.py:105,192,213; models/*.py; seed.py
Description: `Model.query.get(id)` (legado SQLAlchemy 2.0) e `datetime.utcnow()` (deprecado no Python 3.12).
Impact: Uso de APIs obsoletas.
Recommendation: `db.session.get(Model, id)` e `datetime.now(UTC)` (naive UTC equivalente). Playbook P11.

### [MEDIUM] CORS totalmente aberto
File: app.py:15
Description: `CORS(app)` libera todas as origens.
Impact: Superfície de ataque ampliada.
Recommendation: Restringir origens por config.

### [LOW] Dependências declaradas e não usadas / código morto
File: requirements.txt (marshmallow, requests, python-dotenv); services/notification_service.py; utils/helpers.py (arquivo inteiro); models/task.py:38-48, 50-60
Description: Libs nunca importadas; NotificationService nunca usado; `utils/helpers.py` é código
morto integralmente — `format_date` e `calculate_percentage` só aparecem no `import` de
`report_routes.py:7` e nunca são chamados, as outras 7 funções nunca são importadas e as 7
constantes (`VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`,
`MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR`) têm 0 usos; `Task.validate_status`,
`Task.validate_priority` e `Task.is_overdue` também são ignorados pelas rotas.
Impact: Ruído e confusão.
Recommendation: Remover o morto e adotar o que é útil. Playbook L3.

### [LOW] Imports não usados
File: app.py:7 (`os, sys, json`); task_routes.py:7; user_routes.py:6; report_routes.py:7, 8; utils/helpers.py:3-7
Description: `os, sys, json, time, hashlib` etc. importados e não usados. Em `app.py:7` o
`datetime` **é** usado (`app.py:24`), então apenas `os`, `sys` e `json` são supérfluos ali;
em `report_routes.py:7` os helpers `format_date` e `calculate_percentage` são importados e
nunca chamados.
Impact: Falso sinal de dependência — o leitor supõe que os helpers e módulos importados
participam do fluxo, e ferramentas de análise/`grep` os contam como em uso, mascarando o
código morto do finding anterior.
Recommendation: Remover.

### [LOW] Magic numbers/strings espalhados
File: task_routes.py:96-100, 110, 113, 182-183; user_routes.py:64, 71, 115, 120
Description: Constantes existem em utils/helpers.py:110-116 mas são ignoradas: título 3/200 e
prioridade 1-5 literais no create (`96-100`, `113`) e repetidos no update (`182-183`), lista de
status inline (`110`), senha mínima 4 duplicada em cadastro e update (`64`, `115`) e lista de
roles inline duas vezes (`71`, `120`).
Impact: Mudar qualquer uma dessas regras exige caçar o literal em cada rota, com risco de
esquecer um ponto; os mesmos limites já vivem em três lugares (create, update e
`utils/helpers.py`) sem nada que os mantenha sincronizados, e as mensagens de erro repetem os
números à mão, então uma alteração de limite passa a mentir para o cliente da API.
Recommendation: Usar as constantes nomeadas.

### [LOW] `type(x) == list` e returns booleanos verbosos
File: task_routes.py:141,210; utils/helpers.py:103; user.py:34-38; task.py:45-48,50-60
Description: `type(x) == list` em vez de `isinstance`; `if cond: return True else: return False`.
Impact: `type(x) == list` rejeita qualquer subclasse de `list`, então a comparação é frágil por
construção; e o encadeamento de `if/else` retornando booleanos infla `is_overdue` para 11 linhas
(`task.py:50-60`) o que é a razão pela qual as rotas preferiram reescrever a regra inline — vide
o finding de overdue duplicado 6×.
Recommendation: `isinstance` e retornar a expressão.

================================
Total: 23 findings
================================

> Observação: SQLAlchemy parametriza as queries (sem SQL injection clássico). Os riscos
> aqui são MD5/segredos hardcoded, vazamento de hash, debug, e a ausência de camadas
> controller/service apesar da organização parcial.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (autorizado via aprovação do plano e da abordagem de segurança)

================================
ADENDO — 2026-09-01
================================
Achado: a Fase 3 original assinou o token de login com `itsdangerous` (resolvendo a parte
"token forjável" do finding [HIGH] "Autenticação ausente e token forjável"), mas nenhuma rota
de `user_routes.py`, `task_routes.py` ou `category_routes.py` passou a exigi-lo — a
impersonação apontada no finding continuava trivial (qualquer chamador sem token acessava e
alterava dados de qualquer usuário).

Correção: adicionado `middlewares/auth.py` com o guard `login_required` (Playbook P13, novo
no catálogo/playbook da skill — ver `references/02-antipattern-catalog.md` C7/H5 e
`references/05-refactoring-playbook.md`). Aplicado a todas as rotas de `user_routes.py`
(exceto cadastro e login, que permanecem públicos), `task_routes.py`, `category_routes.py` e
`report_routes.py` (mesma falha, não listada no finding original mas mesma causa raiz).
`itsdangerous` adicionado a `requirements.txt` (usado mas não declarado).

Validação: aplicação sobe sem erros; smoke test confirma 401 em todas as rotas protegidas sem
token e com token forjado, 200 com token válido emitido pelo `/login`, e `/health`, `/`,
`POST /users` e `POST /login` seguem públicos.

A skill (`SKILL.md` + playbook) foi reforçada para que a Fase 3 sempre aplique este guard
sempre que a Fase 2 apontar autenticação ausente fora do contexto administrativo — ver
Fase 3, regras obrigatórias. Os outros dois projetos deste repositório (`code-smells-project`,
`ecommerce-api-legacy`) foram reauditados contra o catálogo atualizado: ambos só têm
endpoints administrativos sem sessão de usuário comum, e ambos já protegem esses endpoints
com `admin_required`/`adminGuard` — nenhum gap equivalente encontrado.

Achado adicional (fora do escopo dos findings originais): `set_password()` (`models/user.py`)
usava `generate_password_hash(pwd)` sem fixar o método, herdando o `scrypt` padrão do `werkzeug`
— indisponível em builds de Python sem OpenSSL com suporte a scrypt (reproduzido no Python 3.9 do
sistema em macOS), o que derrubava `POST /users` com 500. Corrigido fixando
`method="pbkdf2:sha256"` (mesma correção aplicada em `code-smells-project`, ver adendo em
`audit-project-1.md`, e documentada no Playbook P4). Revalidado o fluxo completo via API real:
`POST /users` (201) → `POST /login` (200, token) → `GET /tasks` com o token (200) e sem token
(401).

================================
ADENDO — 2026-09-02
================================
Achado 1 — segredo com default versionado: o `SECRET_KEY` passou a vir de config, mas com
fallback `'dev-secret-change-in-production'` no repositório. Como essa chave assina os tokens de
sessão, o default publicado permitia forjar a sessão de qualquer usuário — bastava assinar um
token com a constante conhecida. Não é o mesmo defeito do finding [CRITICAL] "SECRET_KEY
hardcoded", é sua reincidência disfarçada de default de desenvolvimento.

Correção: a aplicação agora falha na inicialização, com mensagem clara, se `SECRET_KEY` não
vier do ambiente; `FLASK_ENV=development` gera uma chave efêmera em memória (perdida a cada
restart, portanto inútil para forjar sessão persistente). Verificado: sem `SECRET_KEY` o
processo aborta; um token forjado com a constante antiga passou a receber 401 — antes devolvia
200 com os dados de todos os usuários.

Achado 2 — inversão de camada na emissão do token: `user_service` importava
`middlewares.auth._serializer`, uma função privada da camada HTTP, invertendo a dependência
(service → middleware). Correção: emissão e leitura do token movidas para
`services/token_service.py`; o middleware passou a consumir o service, não o contrário.

Achado 3 — guard sem revalidação do sujeito: o `login_required` do adendo anterior confiava
apenas na assinatura do token, então um token válido continuava aceito depois de o usuário ser
apagado ou desativado, até expirar. Correção: o guard recarrega o usuário do banco em cada
request e rejeita conta inexistente (401) ou inativa (403).

Achado 4 (o principal desta rodada) — autorização inexistente: o adendo de 2026-09-01 fechou
"quem entra", não "quem pode o quê". O `g.current_user_id` era gravado pelo guard e **nenhuma
camada o lia**, de modo que "estar logado" equivalia a acesso total: qualquer usuário comum
lia, alterava e apagava dados de qualquer outro. Esta é a lacuna central que o relatório
apontava sob [HIGH] "Autenticação ausente e token forjável" e que a Fase 3 só havia resolvido
pela metade.

Correção: autorização implementada em `services/authorization.py` (`require_admin`,
`require_self_or_admin`, `is_admin`), com o usuário atual repassado pelos controllers como
parâmetro `actor`. Os services continuam sem importar `flask`, então seguem testáveis fora de
contexto HTTP. Regras aplicadas:
- `GET /users` e `GET /reports/summary` passaram a exigir admin;
- `GET/PUT/DELETE /users/<id>`, `GET /users/<id>/tasks` e `GET /reports/user/<id>` exigem dono
  ou admin;
- listagem, busca e estatísticas de tasks passaram a ser escopadas ao dono (admin vê tudo);
- reatribuir task para outro usuário e criar task para terceiro tornaram-se ações de admin;
- escrita de categorias (criar/alterar/remover) passou a exigir admin, porque a taxonomia é
  compartilhada e a remoção desvincula tasks de todos os usuários;
- troca da própria senha passou a exigir `current_password` (403 sem ela ou com valor errado);
  admin troca sem esse requisito;
- `active` passou a exigir admin e a validar booleano.

Achado 5 — mass assignment de privilégio: o cadastro público aceitava `role` do corpo da
requisição, então qualquer anônimo se cadastrava como `admin`. Correção: `role` enviado no
cadastro público é IGNORADO e todo usuário nasce como `user` (o cadastro segue respondendo 201);
promover alguém é ação de admin via `PUT /users/<id>`. Verificado: cadastro anônimo pedindo
`role: admin` gravou `user`; usuário comum tentando se promover recebeu 403; admin promovendo
via PUT recebeu 200.

Achado 6 — 500 por validação ausente: quatro caminhos de update respondiam HTTP 500 e agora
respondem 400 — `{"password":null}`, `{"name":null}` e `{"active":"talvez"}` em
`PUT /users/<id>`, e `{"name":null}` em `PUT /categories/<id>`. Complementa o finding [MEDIUM]
"Validação ausente / casts inseguros".

Achado 7 — sessão suja após erro: o tratamento central de erros respondia sem desfazer a
transação, dependendo do teardown do Flask-SQLAlchemy para limpar a sessão. Correção: `db.session.rollback()`
antes de responder.

MUDANÇAS DE CONTRATO (intencionais, não regressões): endpoints antes acessíveis a qualquer
usuário logado agora respondem 403 quando o requisitante não é dono nem admin; `GET /tasks`,
`/tasks/search` e `/tasks/stats` passaram a devolver apenas os dados do próprio usuário (admin
continua vendo tudo). São exatamente as correções pretendidas dos findings de Broken Access
Control.

Validação: os 22 endpoints originais foram exercitados com token de admin e todos responderam
2xx, com 0 respostas 5xx e 0 tracebacks no log; os endpoints protegidos respondem 401 sem
token. Os oito ataques que a auditoria anterior demonstrou como bem-sucedidos (usuária comum
renomeando e rebaixando o admin, apagando task de terceiro, lendo relatório global, listando
e-mails de todos, lendo dados e relatório de outro usuário, alterando task alheia) passaram
todos a responder 403.

Status do finding [MEDIUM] "API deprecated: Query.get e datetime.utcnow": REMEDIADO — não
pendente. Verificação no código atual: 0 ocorrências de `.query.` e 0 de `datetime.utcnow` em
todo o projeto (a única linha que casa `datetime.utcnow` é a docstring que documenta a
substituição). O helper `utcnow()` em `utils/helpers.py:18-21` substituiu a API deprecada, e o
`seed.py` — último ponto que ainda usava a API legada `Model.query` — foi migrado para
`db.session.execute(db.delete(...))` e `db.session.scalar(db.select(func.count())...)`.

Permanecem em aberto, fora do escopo desta rodada: paginação nas listagens (finding [MEDIUM]
"Sem paginação"), `CORS(app)` irrestrito, `NotificationService` como código morto,
`MIN_PASSWORD_LENGTH = 4` e ausência de rate limiting no login.
