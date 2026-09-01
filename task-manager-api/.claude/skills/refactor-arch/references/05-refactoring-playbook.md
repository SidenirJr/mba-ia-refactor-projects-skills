# 05 — Playbook de Refatoração (Fase 3)

Padrões de transformação **antes/depois** para os anti-patterns do catálogo. Cada padrão
mapeia para um ou mais findings. Aplique por ordem de severidade. Os exemplos cobrem
Python/Flask e Node/Express para reforçar o agnosticismo.

> ≥8 padrões exigidos; abaixo há 13 (P1–P13).

---

## P1 — Extrair config/segredos para módulo por ambiente

Resolve: C1 (hardcoded secrets), C6 (debug exposto).

**Antes (Python)**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois**
```python
# config/settings.py
import os
class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]          # falha cedo se faltar
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]
settings = Settings()
# app.py
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
```
**Node:** mover `config` com segredos para `process.env` + `dotenv`; commitar apenas
`.env.example`. Adicione `.env` ao `.gitignore`.

---

## P2 — Eliminar SQL Injection com queries parametrizadas + repository

Resolve: C2 (SQL injection).

**Antes**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")")
```
**Depois (sqlite3 nativo, parametrizado, isolado no repository)**
```python
# models/produto_repository.py
class ProdutoRepository:
    def __init__(self, db): self.db = db
    def get_by_id(self, id):
        return self.db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    def create(self, nome, preco):
        cur = self.db.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
        self.db.commit(); return cur.lastrowid
```
Para filtros dinâmicos, construa a cláusula com placeholders e uma lista de params:
```python
sql, params = "SELECT * FROM produtos WHERE 1=1", []
if termo:     sql += " AND (nome LIKE ? OR descricao LIKE ?)"; params += [f"%{termo}%", f"%{termo}%"]
if categoria: sql += " AND categoria = ?";                      params.append(categoria)
rows = self.db.execute(sql, params).fetchall()
```
**Node (sqlite3):** sempre `db.all("... WHERE id = ?", [id], cb)` / `better-sqlite3`
`stmt.get(id)`. Nunca interpole input em string SQL.

---

## P3 — Quebrar God Class/God File em camadas

Resolve: C3 (God Class).

**Antes (Node — uma classe faz tudo)**
```js
class AppManager {
  constructor(){ this.db = new sqlite3.Database(":memory:"); }
  initDb(){ /* schema + seed */ }
  setupRoutes(app){ app.post("/api/checkout", (req,res)=>{ /* validação + SQL + pagamento + log */ }); }
}
```
**Depois (responsabilidades separadas)**
```
src/
├── config/db.js                 # cria/exporta a conexão (injeção)
├── models/userRepository.js     # SQL parametrizado por entidade
├── services/checkoutService.js  # regra de checkout + transação
├── controllers/checkoutController.js  # HTTP fino
├── routes/checkoutRoutes.js     # router por recurso
└── app.js                       # monta tudo
```
Mova cada bloco para sua camada; o controller chama o service, o service usa os
repositories. Schema/seed saem para um módulo de migração/seed dedicado.

---

## P4 — Hash de senha forte

Resolve: C4 (plaintext/MD5/crypto caseiro).

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()          # quebrado, sem salt
# ou: senha salva/comparada em texto puro
```
**Depois (Python)**
```python
from werkzeug.security import generate_password_hash, check_password_hash
def set_password(self, pwd):
    self.password = generate_password_hash(pwd, method="pbkdf2:sha256")  # não "scrypt" (padrão)
def check_password(self, pwd): return check_password_hash(self.password, pwd)
```
**Node**
```js
const bcrypt = require("bcrypt");
const hash = await bcrypt.hash(pwd, 12);
const ok = await bcrypt.compare(pwd, user.pass);
```
Re-gere os hashes do seed. O login continua funcionando com as mesmas credenciais.

> **Portabilidade:** fixe `method="pbkdf2:sha256"` explicitamente. O padrão do `werkzeug` (`scrypt`)
> depende de `hashlib.scrypt`, que exige Python compilado contra OpenSSL com suporte a scrypt —
> ausente no Python do sistema em algumas instalações macOS (LibreSSL), onde falha com
> `AttributeError: module 'hashlib' has no attribute 'scrypt'` já no boot/seed. `pbkdf2:sha256`
> não tem essa dependência e é aceito por `check_password_hash` da mesma forma.

---

## P5 — Remover dados sensíveis da serialização

Resolve: C5 (sensitive data exposure).

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, "role": self.role}
```
**Depois**
```python
def to_dict(self):   # nunca inclui password/hash
    return {"id": self.id, "email": self.email, "role": self.role}
```
Também: remova `senha` de respostas de listagem (`SELECT` colunas explícitas, sem a de
senha), tire `secret_key` do `/health`, e **nunca** logue cartão/segredo. Em Node, troque
`console.log(\`...cartão ${cc}...\`)` por log sem o PAN/chave.

---

## P6 — Mover lógica de negócio do controller/rota para o service

Resolve: H1 (business logic in controller), M3 (duplicação).

**Antes (lógica e cálculo na rota)**
```python
@bp.route("/relatorios/vendas")
def relatorio_vendas():
    ... # COUNT, SUM, e regra de desconto (10%/5%/2%) calculada aqui
```
**Depois**
```python
# services/relatorio_service.py
class RelatorioService:
    def __init__(self, pedido_repo): self.repo = pedido_repo
    def vendas(self):
        faturamento = self.repo.faturamento_total()
        desconto = self._desconto(faturamento)   # regra isolada e testável
        return {...}
# controllers/relatorio_controller.py
def relatorio_vendas():
    return jsonify({"dados": relatorio_service.vendas(), "sucesso": True}), 200
```
Reutilize lógica já existente em vez de duplicar (ex.: um `Task.is_overdue()` que já existe
deve ser chamado, não reimplementado inline em cada rota).

---

## P7 — Introduzir injeção de dependência / eliminar estado global mutável

Resolve: H2 (no DI), H3 (global state).

**Antes**
```python
db_connection = None           # global mutável
def get_db():
    global db_connection
    if db_connection is None: db_connection = sqlite3.connect(...)
    return db_connection
```
**Depois**
```python
# conexão criada na composição e injetada
repo = ProdutoRepository(db)
service = ProdutoService(repo)
controller = ProdutoController(service)
```
Em Flask, prefira conexão por requisição (`flask.g` + `teardown_appcontext`) ou a sessão do
SQLAlchemy. Em Node, exporte uma conexão criada uma vez e **injete** nos repositories;
elimine caches globais que crescem sem limite.

---

## P8 — Envolver escrita multi-passo em transação

Resolve: H4 (missing transaction).

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
db.commit()   # sem rollback se algo falhar no meio
```
**Depois**
```python
try:
    self.db.execute("BEGIN")
    self.db.execute("INSERT INTO pedidos ...", (...))
    for item in itens:
        self.db.execute("INSERT INTO itens_pedido ...", (...))
        self.db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (...))
    self.db.commit()
except Exception:
    self.db.rollback(); raise
```
**Node:** `db.run("BEGIN")` … `COMMIT`/`ROLLBACK`, ou `db.transaction(...)` do
better-sqlite3. Em checkout (matrícula+pagamento+log), tudo numa transação.

---

## P9 — Corrigir N+1 com JOIN / eager-load / agregação

Resolve: M1 (N+1).

**Antes**
```python
for pedido in pedidos:
    itens = query("SELECT * FROM itens_pedido WHERE pedido_id = ?", pedido.id)
    for item in itens:
        prod = query("SELECT nome FROM produtos WHERE id = ?", item.produto_id)
```
**Depois (uma query com JOIN)**
```python
rows = self.db.execute("""
    SELECT p.id AS pedido_id, ip.produto_id, pr.nome, ip.quantidade, ip.preco_unitario
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
""").fetchall()
# agrupe em memória por pedido_id
```
**SQLAlchemy:** `select(Task).options(joinedload(Task.user), joinedload(Task.category))`,
ou `func.count()` agregado em vez de N `count()` separados.

---

## P10 — Validação centralizada + error handler

Resolve: M2 (validação), M4 (middleware/erro).

**Antes:** validação manual repetida e `except Exception: return 500` em cada handler,
vazando `str(e)`.
**Depois**
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _v(e): return jsonify({"erro": str(e)}), 400
    @app.errorhandler(Exception)
    def _e(e): app.logger.exception(e); return jsonify({"erro": "Erro interno"}), 500
```
Centralize a validação em schemas (marshmallow/pydantic) ou helpers reutilizáveis; pare de
vazar stack/erro do driver ao cliente. **Node:** middleware `(err, req, res, next)` único no
fim da cadeia.

---

## P11 — Substituir APIs deprecated e print()→logger

Resolve: M6 (logging) + seção de deprecated do catálogo.

```python
# deprecated → moderno
Task.query.get(id)          →  db.session.get(Task, id)
datetime.utcnow()           →  datetime.now(datetime.UTC)
print("Task criada", id)    →  logger.info("Task criada id=%s", id)
```
```js
// Express
const bodyParser = require("body-parser"); app.use(bodyParser.json());  // antigo
app.use(express.json());                                                // moderno
// callbacks → async/await + Promise.all
```
Use o `logging` do Python / um logger (pino/winston) no Node, com níveis.

---

## P12 — Proteger endpoint administrativo com admin guard (mantendo-o vivo)

Resolve: C7 (broken access control) quando o recurso é **administrativo/destrutivo**
(reset de DB, SQL arbitrário, relatórios financeiros amplos, delete em massa) — ação que só
faz sentido para um papel privilegiado, não para qualquer usuário logado. Se o problema é
"nenhum endpoint exige sessão" de forma geral, use **P13**, não este.

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"]); ...   # SQL arbitrário, sem auth
```
**Depois (endpoint continua existindo, agora protegido)**
```python
# middlewares/auth.py
from functools import wraps
def admin_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if request.headers.get("X-Admin-Token") != settings.ADMIN_TOKEN:
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*a, **k)
    return wrapper

@admin_required
def executar_query(): ...
```
Aplique o mesmo guard a reset de DB, relatórios financeiros e delete destrutivo. Para tokens
de sessão forjáveis (`'fake-jwt-token-'+id`), prefira um token assinado/expirável (ver P13);
no mínimo, documente o risco e isole a geração do token num service.

---

## P13 — Exigir login em endpoints de usuário autenticado (login guard)

Resolve: C7 (broken access control) e H5 (fake/forgeable token) quando o finding é mais
amplo que um endpoint admin isolado: **nenhuma rota de recurso do usuário logado** (tasks,
categorias, o próprio perfil, relatórios pessoais, etc.) exige sessão válida — qualquer um
pode ler/alterar/apagar dados de qualquer usuário só sabendo o id. Este é o guard **padrão**
a aplicar sempre que a Fase 2 apontar "autenticação ausente"/"token forjável" fora do
contexto administrativo — P12 é a exceção para rotas de admin, não o padrão geral.

**Antes**
```python
# login gera um token, mas nenhuma rota o valida
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    ...   # qualquer requisição sem token apaga qualquer usuário
```
**Depois (token assinado + guard aplicado a toda rota que exige usuário logado)**
```python
# services/user_service.py — geração do token no login (assinado, expirável)
from itsdangerous import URLSafeTimedSerializer

def _serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="auth-token")

token = _serializer().dumps({"user_id": user.id})   # nunca 'fake-jwt-token-'+id

# middlewares/auth.py — guard reaproveitável por qualquer rota autenticada
from functools import wraps
from flask import g, request
from itsdangerous import BadSignature, SignatureExpired
from config.settings import settings
from errors import UnauthorizedError

def _serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="auth-token")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else header
        if not token:
            raise UnauthorizedError("Token de autenticação ausente")
        try:
            data = _serializer().loads(token, max_age=settings.TOKEN_MAX_AGE)
        except (BadSignature, SignatureExpired):
            raise UnauthorizedError("Token inválido ou expirado")
        g.current_user_id = data["user_id"]
        return f(*args, **kwargs)
    return wrapper
```
```python
# routes/*.py — aplique o guard na registration, não dentro do controller
user_bp.add_url_rule("/users/<int:user_id>", "delete_user",
                      login_required(user_controller.delete_user), methods=["DELETE"])
# criação de conta e login continuam públicos — são o meio de OBTER o token
user_bp.add_url_rule("/users", "create_user", user_controller.create_user, methods=["POST"])
user_bp.add_url_rule("/login", "login", user_controller.login, methods=["POST"])
```
Aplique `login_required` a **todas** as rotas de recursos do usuário autenticado (tasks,
categorias, perfil, relatórios pessoais) nos blueprints correspondentes, deixando públicas
apenas `POST /login` e o cadastro (`POST /users` ou equivalente). `login_required` e
`admin_required` **não são mutuamente exclusivos**: uma rota administrativa pode compor os
dois (`admin_required(login_required(handler))`) quando o projeto tiver papéis/roles.
