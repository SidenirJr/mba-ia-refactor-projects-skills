# 05 — Playbook de Refatoração (Fase 3)

Padrões de transformação **antes/depois** para os anti-patterns do catálogo. Cada padrão
mapeia para um ou mais findings. Aplique por ordem de severidade. Os exemplos cobrem
Python/Flask e Node/Express para reforçar o agnosticismo.

> ≥8 padrões exigidos; abaixo há 15 (P1–P15).

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

**Antes (validação ad-hoc repetida + `except` nu vazando detalhe interno)**
```python
@bp.route("/categorias/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Categoria não encontrada"}), 404

    data = request.get_json()        # body ausente/inválido -> data = None
    if "name" in data:               # TypeError: argument of type 'NoneType' -> 500 opaco
        cat.name = data["name"]
    if "color" in data:
        cat.color = data["color"]

    try:
        db.session.commit()
        return jsonify(cat.to_dict()), 200
    except:                          # except nu: mascara a causa, captura até KeyboardInterrupt
        db.session.rollback()
        return jsonify({"error": "Erro ao atualizar"}), 500


@bp.route("/usuarios", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:                 return jsonify({"error": "Dados inválidos"}), 400
    if not data.get("name"):     return jsonify({"error": "Nome é obrigatório"}), 400
    if not data.get("email"):    return jsonify({"error": "Email é obrigatório"}), 400
    if not data.get("password"): return jsonify({"error": "Senha é obrigatória"}), 400
    if not re.match(EMAIL_RE, data["email"]):
        return jsonify({"error": "Email inválido"}), 400   # bloco copiado em create/update
    try:
        db.session.add(user); db.session.commit()
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500   # vaza SQL/driver ao cliente
```
**Depois**
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _v(e): return jsonify({"erro": str(e)}), 400
    @app.errorhandler(Exception)
    def _e(e): app.logger.exception(e); return jsonify({"erro": "Erro interno"}), 500
```
```python
# controllers/*.py — body opcional nunca estoura; quem decide o que é válido é o service/schema
def update_category(cat_id):
    return jsonify(service.update(cat_id, request.get_json(silent=True) or {})), 200
```
Centralize a validação em schemas (marshmallow/pydantic) ou helpers reutilizáveis; troque
`except:` nu por exceções de domínio (`ValidationError`, `NotFoundError`) tratadas pelo handler
central, e pare de vazar stack/erro do driver ao cliente. **Node:** middleware
`(err, req, res, next)` único no fim da cadeia.

---

## P11 — Substituir APIs deprecated e print()→logger

Resolve: M6 (logging) + seção de deprecated do catálogo.

**Antes**
```python
Task.query.get(id)                       # Query API legada (SQLAlchemy 2.x)
datetime.utcnow()                        # naive; deprecated no Python 3.12+
print("Task criada", id)                 # sem nível, sem estrutura, sem destino
```
```js
const bodyParser = require("body-parser"); app.use(bodyParser.json());  // Express < 4.16
db.all(sql, [], function (err, rows) { /* pirâmide de callbacks */ });
```
**Depois**
```python
db.session.get(Task, id)
datetime.now(datetime.UTC)               # timezone-aware
logger.info("Task criada id=%s", id)
```
```js
app.use(express.json());
const rows = await allAsync(sql);        // async/await + Promise.all
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

> **P13 não encerra C7 sozinho.** O guard responde *quem é* o requisitante e grava esse
> usuário no contexto (`g.current_user_id`, `req.user`). Se nenhuma camada consultar esse
> valor, qualquer usuário logado continua alcançando o recurso de qualquer outro. Siga
> obrigatoriamente com **P15** (autorização por dono).

---

## P14 — Substituir verificação de negócio fake por checagem real (sandbox)

Resolve: H6 (fake business/domain verification) — decisões de negócio sensíveis (pagamento,
crédito, elegibilidade) hoje decididas por uma heurística sem relação com a verificação real.
**Não é o mesmo problema de P13**: P13 valida *quem é o usuário* (identidade/sessão); P14
valida *se a operação de negócio em si é legítima* — mover o código para uma classe/service
(P3/P6) sem trocar a lógica **não fecha o finding**, só reorganiza o mesmo bug.

**Antes (Node — "aprova" pagamento pela bandeira do cartão)**
```js
class PaymentGateway {
  async charge(card, amount) {
    const status = card.startsWith("4") ? "PAID" : "DENIED";  // qualquer Visa passa
    return { status, amount };
  }
}
```
**Depois (validação estrutural real + casos de teste determinísticos, como um gateway real em
modo sandbox)**
```js
// Cartões de teste que o "emissor" simulado sempre recusa — mesma convenção usada por
// gateways reais em sandbox (ex.: Stripe), Luhn-válidos mas reservados para o caminho de erro.
const DECLINED_TEST_CARDS = new Set(["4000000000000002", "4000000000009995"]);

function isLuhnValid(card) {
  const digits = String(card).replace(/\D/g, "");
  if (digits.length < 12 || digits.length > 19) return false;
  let sum = 0, dbl = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits.charCodeAt(i) - 48;
    if (dbl) { d *= 2; if (d > 9) d -= 9; }
    sum += d; dbl = !dbl;
  }
  return sum % 10 === 0;
}

class PaymentGateway {
  async charge(card, amount) {
    if (!isLuhnValid(card)) return { status: "DENIED", reason: "invalid_card_number", amount };
    if (DECLINED_TEST_CARDS.has(String(card).replace(/\D/g, "")))
      return { status: "DENIED", reason: "card_declined", amount };
    return { status: "PAID", amount };
  }
}
```
**Python (mesmo princípio — nunca aprovar por heurística superficial):**
```python
def is_valid_cpf(cpf):  # exemplo de outro domínio: "if len(cpf) == 11: aprovado" é o mesmo bug
    digits = [int(c) for c in cpf if c.isdigit()]
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    for i in (9, 10):
        total = sum(d * w for d, w in zip(digits[:i], range(i + 1, 1, -1)))
        digito = (total * 10 % 11) % 10
        if digito != digits[i]:
            return False
    return True
```
O princípio se generaliza a qualquer "verificação" de negócio: se a regra real é conhecida
(Luhn para cartão, dígito verificador de CPF/CNPJ, faixa etária com documento, etc.), implemente
essa regra — não um atalho que aprova com base em um padrão previsível e adivinhável pelo
usuário. Quando não há como validar contra um provedor real (sandbox/exercício), documente e
use uma lista fixa e pequena de casos de teste conhecidos para os caminhos de erro, como fazem
gateways de pagamento reais em ambiente de teste.

---

## P15 — Autorização por dono (fim do IDOR)

Resolve: C7 (broken access control), caso **(c)** — o mais comum: o requisitante *está*
autenticado, mas nada verifica se o recurso pedido é dele. **Autenticar** responde *quem é*
(P13); **autorizar** responde *o que essa pessoa pode alcançar* (P15). Um guard que captura o
usuário atual no contexto e nunca é consultado por nenhuma camada **não é proteção** — ele
transforma "estar logado" em acesso total. Aplique P15 sempre depois de P13.

**Quando aplicar:** o guard de sessão existe (ou acabou de ser introduzido por P13) e mesmo
assim `GET /<recurso>/<id>` de outro dono responde 200; `GET /<recurso>` devolve os registros
de todo mundo; `PUT /users/<id>` aceita `role` do corpo; o cadastro público aceita
`role: "admin"`; a troca de senha não exige a senha atual. Sinais de grep: o middleware grava
`g.current_user_id` / `req.user` e nenhum service ou controller lê esse valor; existe um
helper de papel (`is_admin()`) definido e nunca chamado.

**Antes (Python — autenticado é tratado como autorizado)**
```python
# middlewares/auth.py — o guard grava o usuário atual... e ninguém consulta o valor
def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        g.current_user_id = _read_token()     # gravado e nunca lido
        return f(*a, **k)
    return wrapper

# services/task_service.py — o service enxerga o mundo inteiro
class TaskService:
    def list_all(self):                        # devolve as tasks de TODOS os usuários
        return [t.to_dict() for t in db.session.execute(db.select(Task)).scalars()]

    def get(self, task_id):
        task = db.session.get(Task, task_id)   # sem checar dono -> IDOR por id
        if not task:
            raise NotFoundError("Task não encontrada")
        return task.to_dict()

    def update(self, task_id, data):
        task = db.session.get(Task, task_id)
        if "user_id" in data:
            task.user_id = data["user_id"]     # qualquer um reatribui o dono
        ...

# services/user_service.py
class UserService:
    def create(self, data):
        return User(role=data.get("role", "user"))   # mass assignment: anônimo vira admin

    def update(self, user_id, data):
        if "password" in data:
            user.set_password(data["password"])      # troca senha sem exigir a atual
        if "role" in data:
            user.role = data["role"]                 # escala privilégio sem checar papel
```

**Depois — 1. módulo de política, puro e testável (sem `flask`/`req`)**
```python
# services/authorization.py
from errors import ForbiddenError

def is_admin(actor):
    return bool(actor is not None and actor.is_admin())

def require_admin(actor, message="Requer privilégio de administrador"):
    if not is_admin(actor):
        raise ForbiddenError(message)

def require_self_or_admin(actor, owner_id, message="Acesso negado a recurso de outro usuário"):
    if actor is None:
        raise ForbiddenError("Requisição sem usuário autenticado")
    if actor.is_admin() or actor.id == owner_id:
        return
    raise ForbiddenError(message)
```

**2. o guard expõe o usuário; o *controller* o repassa como `actor`**
```python
# middlewares/auth.py
def current_user():
    return getattr(g, "current_user", None)

# controllers/task_controller.py — controller continua fino, mas é ele que injeta o actor
def get_task(task_id):
    return jsonify(service.get(task_id, current_user())), 200
```
> O service **não** lê `flask.g` / `req.user`: recebe `actor` por parâmetro. Assim a camada de
> negócio segue testável sem request (`service.get(1, actor=usuario_falso)`) e a política de
> acesso fica explícita na assinatura, não escondida num global de transporte.

**3. escopo de dono em TODA leitura — listagem, busca e agregações incluídas**
```python
class TaskService:
    def _visible(self, stmt, actor):
        """Restringe a consulta ao que o requisitante pode ver."""
        if is_admin(actor):
            return stmt
        if actor is None:
            raise NotFoundError("Task não encontrada")
        return stmt.where(Task.user_id == actor.id)

    def _require_visible(self, task_id, actor):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        require_self_or_admin(actor, task.user_id, "Acesso negado a task de outro usuário")
        return task

    def list_all(self, actor):
        stmt = self._visible(db.select(Task), actor)
        return [t.to_dict() for t in db.session.execute(stmt).scalars()]

    def get(self, task_id, actor):
        return self._require_visible(task_id, actor).to_dict()

    def search(self, actor, query=None, user_id=None):
        stmt = self._visible(db.select(Task), actor)
        if user_id:                                  # filtrar pelo dono de outra pessoa
            require_self_or_admin(actor, int(user_id))
            stmt = stmt.where(Task.user_id == int(user_id))
        ...

    def stats(self, actor):                          # agregação também é leitura
        base = self._visible(db.select(func.count()).select_from(Task), actor)
        return {"total": db.session.scalar(base) or 0}
```
> Proteger só o acesso por id **não fecha o vazamento**: `GET /tasks` devolvendo tudo, uma
> busca sem cláusula de dono ou um `/stats` global expõem exatamente os mesmos dados.

**4. dono na escrita: quem cria é dono; reatribuir é ação de admin**
```python
    def _resolve_owner(self, data, actor):
        """Dono do recurso novo: o próprio requisitante, exceto se um admin indicar outro."""
        if "user_id" in data and data["user_id"] is not None:
            if actor is None or data["user_id"] != actor.id:
                require_admin(actor, "Apenas um administrador pode criar para outro usuário")
            return data["user_id"]
        return actor.id if actor else None

    def update(self, task_id, data, actor):
        task = self._require_visible(task_id, actor)
        if "user_id" in data and data["user_id"] != task.user_id:
            require_admin(actor, "Apenas um administrador pode reatribuir o dono")
            task.user_id = data["user_id"]
        ...
```

**5. campos de privilégio e troca de senha**
```python
class UserService:
    def create(self, data):
        # Cadastro é rota PÚBLICA: `role` vindo do cliente é IGNORADO e todo mundo nasce
        # como 'user'. Promover alguém é ação de admin, via PUT /users/<id>.
        role = "user"
        ...

    def list_all(self, actor):
        require_admin(actor)          # listar e-mail de todos é dado de administração

    def update(self, user_id, data, actor):
        require_self_or_admin(actor, user_id)
        user = self._require(user_id)
        if "password" in data:
            if not is_admin(actor):
                # Sem exigir a senha atual, uma sessão vazada vira takeover permanente da conta.
                atual = data.get("current_password")
                if not atual or not user.check_password(atual):
                    raise ForbiddenError("Senha atual obrigatória para alterar a senha")
            user.set_password(data["password"])
        if "role" in data:
            require_admin(actor, "Apenas um administrador pode alterar o role")
        if "active" in data:
            require_admin(actor, "Apenas um administrador pode ativar/desativar um usuário")
```

**Node/Express — mesma política, mesma passagem de `actor`**
```js
// services/authorization.js — puro, sem conhecer req/res
const isAdmin = (actor) => Boolean(actor && actor.role === "admin");
function requireAdmin(actor) {
  if (!isAdmin(actor)) throw new ForbiddenError("Requer privilégio de administrador");
}
function requireSelfOrAdmin(actor, ownerId) {
  if (!actor) throw new ForbiddenError("Requisição sem usuário autenticado");
  if (isAdmin(actor) || actor.id === ownerId) return;
  throw new ForbiddenError("Acesso negado a recurso de outro usuário");
}

// routes/taskRoutes.js — o guard autentica, o controller injeta req.user como actor
router.get("/tasks", loginRequired, (req, res, next) =>
  taskService.listAll(req.user).then((r) => res.json(r)).catch(next));

// services/taskService.js — recebe actor; nunca lê req
async function listAll(actor) {
  return isAdmin(actor) ? repo.findAll() : repo.findByOwner(actor.id);  // escopo na LISTAGEM
}
async function get(id, actor) {
  const task = await repo.findById(id);
  if (!task) throw new NotFoundError("Task não encontrada");
  requireSelfOrAdmin(actor, task.userId);                              // fim do IDOR por id
  return task;
}
async function update(id, data, actor) {
  const task = await get(id, actor);
  if ("userId" in data && data.userId !== task.userId) requireAdmin(actor);
  return repo.update(id, data);
}
```

**Validação obrigatória — caminho negativo por dono, não só por token.** Com dois usuários A
e B: `GET /<recurso>/<id-de-B>` autenticado como A responde 403 (ou 404, se você optar por não
revelar existência); `GET /<recurso>` como A não contém nenhum registro de B; `PUT /users/<id-de-A>`
com `{"role": "admin"}` responde 403; cadastro público com `{"role": "admin"}` cria um `user`;
`PUT /users/<id-de-A>` com `{"password": "nova"}` sem `current_password` responde 403. Um smoke
test que só compara "sem token → 401 / com token → 2xx" **não detecta IDOR**.

Ver catálogo: **C7** (Broken Access Control), caso (c). P13 fecha a autenticação, P15 fecha a
autorização — aplicar só P13 deixa o finding aberto.
