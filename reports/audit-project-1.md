```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (versão não fixada no repositório)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1 (sqlite3 via stdlib, não declarado)
Domain:        API de E-commerce (produtos, usuários, pedidos, itens_pedido) com login,
               relatório de vendas, health check e endpoints administrativos
Architecture:  Monolítica — 4 arquivos, camadas só no nome; app.py também executa SQL direto
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 8 | HIGH: 5 | MEDIUM: 7 | LOW: 3

## Findings

### [CRITICAL] SQL Injection generalizada
File: models.py:28, 47-50, 57-61, 68, 92, 110-111, 127-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 280-281, 289-297
Description: Todas as queries são montadas por concatenação de strings com input do usuário (ex.: `"SELECT * FROM produtos WHERE id = " + str(id)`; filtro `" AND nome LIKE '%" + termo + "%'"`).
Impact: Leitura/alteração/destruição completa do banco; bypass de regras via payload malicioso.
Recommendation: Isolar acesso a dados em repositories com queries parametrizadas (placeholders `?`). Playbook P2.

### [CRITICAL] Bypass de autenticação via SQL Injection no login
File: models.py:109-111
Description: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` permite login com `' OR '1'='1`.
Impact: Qualquer pessoa autentica como qualquer usuário.
Recommendation: Query parametrizada + verificação de hash de senha. Playbook P2 + P4.

### [CRITICAL] Endpoint de SQL arbitrário sem autenticação
File: app.py:59-78
Description: `POST /admin/query` executa qualquer SQL recebido no corpo (`cursor.execute(query)`).
Impact: Comprometimento total do banco, sem qualquer auth.
Recommendation: Proteger com guard de admin (token via env), mantendo o endpoint vivo. Playbook P12.

### [CRITICAL] Endpoint destrutivo de reset sem autenticação
File: app.py:47-57
Description: `POST /admin/reset-db` apaga todas as linhas de todas as tabelas sem auth.
Impact: Perda total de dados por qualquer requisição anônima.
Recommendation: Guard de admin (token via env). Playbook P12.

### [CRITICAL] Senhas em texto puro (armazenadas, comparadas e seedadas)
File: models.py:127-129, 110-111; database.py:76-78
Description: Senha é inserida e comparada em texto puro; o seed grava `admin123`, `123456`, `senha123` sem hash.
Impact: Vazamento do banco compromete todas as contas.
Recommendation: Hash com `werkzeug.security` (generate/check_password_hash). Playbook P4.

### [CRITICAL] Exposição de senhas nas respostas da API
File: models.py:83, 99
Description: `get_todos_usuarios`/`get_usuario_por_id` incluem `"senha": row["senha"]`, expostos por `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Dump das senhas de todos os usuários para qualquer chamador.
Recommendation: Serialização que omite campos sensíveis (selecionar colunas explícitas). Playbook P5.

### [CRITICAL] SECRET_KEY hardcoded e vazado via /health
File: app.py:7; controllers.py:289
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` no código e devolvido pelo `/health` (`"secret_key": ...`), junto de `debug`, `db_path` e `ambiente: "producao"`.
Impact: Segredo versionado e exposto publicamente sem auth.
Recommendation: Config por variável de ambiente; remover o segredo do payload do /health. Playbook P1 + P5.

### [CRITICAL] Debug mode ligado e exposto em 0.0.0.0
File: app.py:8, 88
Description: `DEBUG=True` e `app.run(host="0.0.0.0", debug=True)` com ambiente marcado como produção.
Impact: Console interativo do Werkzeug → execução remota de código (RCE).
Recommendation: DEBUG via env, default desligado; servidor WSGI em produção. Playbook P1.

### [HIGH] God file / colapso de camadas em app.py
File: app.py:11-30, 47-78
Description: app.py é roteador, config e também controller+DAL — `reset_database` e `executar_query` abrem cursor e rodam SQL direto, ignorando controllers/models.
Impact: Responsabilidades misturadas; impossível testar/isolar.
Recommendation: Separar em config, views, controllers, services, repositories e composition root. Playbook P3.

### [HIGH] Lógica de negócio dentro do controller
File: controllers.py:208-210, 247-250
Description: Disparo de "notificações" (e-mail/SMS/push) e regras de status embutidos no handler HTTP.
Impact: Lógica acoplada ao transporte; não reutilizável nem testável.
Recommendation: Mover para um service de pedidos/notificações. Playbook P6.

### [HIGH] Lógica de negócio dentro da camada de dados
File: models.py:256-262
Description: Cálculo das faixas de desconto (10%/5%/2%) embutido na função de "model".
Impact: Regra de domínio misturada com acesso a dados.
Recommendation: Mover o cálculo para um RelatorioService. Playbook P6.

### [HIGH] Estado global mutável para a conexão de banco
File: database.py:4-10
Description: Conexão singleton global com `check_same_thread=False` compartilhada entre threads.
Impact: Race conditions e cursores compartilhados sob concorrência.
Recommendation: Conexão por requisição (`flask.g` + teardown) injetada nos repositories. Playbook P7.

### [HIGH] Sem injeção de dependência / acoplamento forte
File: controllers.py:2-3; models.py:1
Description: Camadas se importam estaticamente sem abstração/repository.
Impact: Substituição e teste com fakes impossíveis.
Recommendation: Injetar repositories nos services e services nos controllers. Playbook P7.

### [HIGH] Criação de pedido não atômica (sem rollback)
File: models.py:133-169
Description: Insere pedido, depois itens e baixa de estoque em loop, com um único commit no fim e sem try/rollback.
Impact: Falha no meio deixa pedido parcial / estoque inconsistente.
Recommendation: Envolver em transação (BEGIN/COMMIT/ROLLBACK). Playbook P8.

### [MEDIUM] Queries N+1 na listagem de pedidos
File: models.py:171-201, 203-233
Description: Para cada pedido, query de itens; para cada item, query do nome do produto.
Impact: Número de consultas cresce linearmente; degrada performance.
Recommendation: Substituir por um único JOIN e agrupar em memória. Playbook P9.

### [MEDIUM] Validação de entrada ausente/fraca
File: controllers.py:39-46, 118, 146-165, 239-240; models.py:140
Description: Sem checagem de tipo de `preco`/`estoque`; `if preco_min:` descarta `0` (falsy); criar_usuario não valida formato de email; criar_pedido quebra com item sem `produto_id`.
Impact: 500s e dados inválidos.
Recommendation: Validação centralizada/reutilizável e checagem de tipos. Playbook P10.

### [MEDIUM] Vazamento de exceção interna ao cliente
File: controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 255, 262, 292
Description: Todo handler termina com `except Exception as e: return jsonify({"erro": str(e)}), 500`.
Impact: Detalhe de stack/driver exposto (information disclosure).
Recommendation: Error handler central com resposta padronizada e log interno. Playbook P10.

### [MEDIUM] Duplicação de código
File: controllers.py:28-50 vs 72-90; models.py:4-22 vs 31-40 vs 304-313; models.py:171-201 vs 203-233
Description: Blocos de validação e mapeamento row→dict repetidos; lógica de fetch de pedidos duplicada.
Impact: Manutenção multiplicada e correções esquecidas.
Recommendation: Extrair helpers/serializers e reusar. Playbook P6.

### [MEDIUM] CORS totalmente aberto
File: app.py:9
Description: `CORS(app)` libera todas as origens, inclusive admin e login.
Impact: Superfície de ataque ampliada.
Recommendation: Restringir origens por config.

### [MEDIUM] print() usado como logging
File: app.py:56, 83-86; controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: Rastreamento de fluxo, erros e eventos via `print`.
Impact: Sem níveis/estrutura/destino configurável.
Recommendation: Módulo `logging` / `app.logger`. Playbook P11.

### [MEDIUM] Sem paginação nas listagens
File: models.py:4-22, 72-87, 203-233
Description: Listagens retornam a tabela inteira.
Impact: Não escala; payloads potencialmente enormes.
Recommendation: Parâmetros limit/offset no repository.

### [MEDIUM] API deprecated: persistência por SQL cru montado à mão
File: models.py (todas as funções)
Description: Uso de `sqlite3` com SQL concatenado em vez de queries parametrizadas (que o próprio projeto usa corretamente em database.py:70-73).
Impact: Inseguro e antiquado.
Recommendation: Queries parametrizadas (ou ORM). Equivalente moderno: `cursor.execute(sql, params)`. Playbook P2/P11.

### [LOW] Magic numbers e literais soltos
File: models.py:257-262; controllers.py:47-50, 52, 242; app.py:36
Description: Faixas/taxas de desconto, limites de nome, listas de categoria/status e versão duplicada hardcoded.
Recommendation: Constantes nomeadas / config. Playbook L1.

### [LOW] Sombreamento do builtin `id`
File: controllers.py:14, 64, 98, 136; models.py:24, 54, 65, 89
Description: Parâmetro chamado `id` em várias funções.
Recommendation: Renomear (ex.: `produto_id`).

### [LOW] Concatenação de strings em vez de f-strings
File: controllers.py:8; models.py:48-49
Description: `"... " + str(x)` por todo o código (também contribui para o smell de injeção).
Recommendation: f-strings / parametrização.

================================
Total: 23 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (autorizado via aprovação do plano e da abordagem de segurança)

================================
ADENDO — 2026-09-01
================================
Achado (fora do escopo dos findings acima): `generate_password_hash()` (Playbook P4, usado no
seed de `src/models/database.py` e em `src/services/usuario_service.py`) usa por padrão o método
`scrypt` do `werkzeug`, que depende de `hashlib.scrypt` — indisponível em builds de Python sem
OpenSSL com suporte a scrypt (reproduzido no Python 3.9 do sistema em macOS/LibreSSL 2.8.3). Como
o seed roda dentro de `init_db()`, o efeito era o **boot inteiro falhar**, não apenas o hashing.

Correção: fixado `method="pbkdf2:sha256"` nos dois pontos de hashing. `check_password_hash`
permanece compatível com qualquer método, então não há impacto em credenciais existentes.
Revalidado: boot limpo + `POST /login`, `GET /produtos`, `GET /usuarios`, `/admin/query` (401 sem
token, 200 com token) e `/admin/reset-db` (401 sem token) testados via API real. Nota de
portabilidade adicionada ao Playbook P4 da skill (sincronizada nos 3 projetos).
