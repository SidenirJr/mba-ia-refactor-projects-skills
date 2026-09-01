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
Source files:  15 .py files analyzed (~1000 linhas)
DB tables:     users, tasks, categories (SQLite, sqlite:///tasks.db)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   15 analyzed | ~1000 lines of code

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 8 | LOW: 4

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
File: routes/task_routes.py, routes/user_routes.py, routes/report_routes.py (todas)
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
Description: ~13 `count()` separados no relatório e 5 counts + reload de todas as tasks no stats.
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
File: task_routes.py:14, 266; user_routes.py:12; report_routes.py
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
File: requirements.txt (marshmallow, requests, python-dotenv); services/notification_service.py; utils/helpers.py (maioria); models/task.py:38-48
Description: Libs nunca importadas; NotificationService nunca usado; helpers/constantes e `validate_*`/`is_overdue` ignorados.
Impact: Ruído e confusão.
Recommendation: Remover o morto e adotar o que é útil. Playbook L3.

### [LOW] Imports não usados
File: app.py:7; task_routes.py:7; user_routes.py:6; report_routes.py:8; utils/helpers.py:3-7
Description: `os, sys, json, time, hashlib` etc. importados e não usados.
Recommendation: Remover.

### [LOW] Magic numbers/strings espalhados
File: task_routes.py e user_routes.py (prioridades 1-5, título 3/200, senha min 4, status)
Description: Constantes existem em utils/helpers.py:110-116 mas são ignoradas.
Recommendation: Usar as constantes nomeadas.

### [LOW] `type(x) == list` e returns booleanos verbosos
File: task_routes.py:141,210; utils/helpers.py:103; user.py:34-38; task.py:45-48,50-60
Description: `type(x) == list` em vez de `isinstance`; `if cond: return True else: return False`.
Recommendation: `isinstance` e retornar a expressão.

================================
Total: 22 findings
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
