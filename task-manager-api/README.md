# task-manager-api

API de gerenciamento de tarefas em Python/Flask + SQLAlchemy. O projeto já tinha alguma
organização (models/routes/services/utils); a skill `refactor-arch` introduziu as camadas
**controller** e **service** que faltavam e corrigiu segurança/performance.

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # ajuste os valores (opcional em dev)
python seed.py              # popula dados de exemplo (rode antes do 1º boot)
python app.py
```

A aplicação sobe em `http://localhost:5000`. As senhas são hasheadas com `werkzeug`.

## Estrutura (MVC em camadas)

```
app.py                       # composition root (app-factory) + entry point
database.py                  # instância SQLAlchemy (db)
config/settings.py           # configuração por ambiente (sem segredos hardcoded)
models/                      # entidades SQLAlchemy (Task, User, Category)
controllers/                 # handlers HTTP finos (NOVO)
services/                    # regras de negócio + agregações (NOVO: task/user/category/report)
routes/                      # blueprints (View) — inclui category_routes (NOVO)
middlewares/error_handler.py # tratamento de erros central (NOVO)
utils/helpers.py             # constantes e helpers (agora realmente usados)
errors.py                    # exceções de domínio
```

## Principais melhorias

- Camadas **controller + service** (lógica saiu das rotas).
- Senhas: **MD5 → werkzeug**; hash **removido** das respostas.
- Login com **token assinado** (itsdangerous) no lugar do `fake-jwt-token`.
- N+1 eliminado com **eager loading** e **queries agregadas** (GROUP BY).
- APIs deprecated trocadas: `Model.query.get` → `db.session.get`; `datetime.utcnow()` → helper `utcnow()`.
- Categorias movidas para `category_routes`/`category_controller` (paths `/categories` preservados).
- Config/segredos (SECRET_KEY, SMTP) via ambiente; CORS e debug configuráveis.

Endpoints originais preservados (tasks, users, login, categories, reports, health).
