# 01 — Análise de Projeto (Fase 1)

Heurísticas **agnósticas de tecnologia** para detectar linguagem, framework, banco de
dados, domínio e arquitetura. Funcione por evidência: leia os arquivos-marcador primeiro,
depois confirme no código-fonte.

## 1. Detecção de linguagem e versão

| Evidência (arquivo-marcador) | Linguagem | Como achar a versão |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python | `python_requires`, `.python-version`, `runtime.txt`; senão, reporte "não fixada" |
| `package.json`, `*.js`, `*.ts` | JavaScript/Node (TypeScript se houver `tsconfig.json`) | campo `engines.node`; senão "não fixada" |
| `pom.xml`, `build.gradle`, `*.java` | Java | `maven.compiler.source` / `sourceCompatibility` |
| `go.mod`, `*.go` | Go | diretiva `go` no `go.mod` |
| `Gemfile`, `*.rb` | Ruby | `.ruby-version` / `Gemfile` |
| `composer.json`, `*.php` | PHP | `require.php` |

Se a versão não estiver fixada em lugar nenhum, isso já é um finding LOW (falta de
reprodutibilidade) — registre.

## 2. Detecção de framework e dependências

Leia o manifesto de dependências e identifique o framework web e libs relevantes:

- **Python:** `flask`, `django`, `fastapi`, `flask-sqlalchemy`, `flask-cors`,
  `sqlalchemy`, `marshmallow`, `pydantic`, `requests`, `python-dotenv`.
- **Node:** `express`, `koa`, `fastify`, `nestjs`, `sqlite3`, `better-sqlite3`, `pg`,
  `mongoose`, `sequelize`, `prisma`, `bcrypt`, `dotenv`, `helmet`, `cors`.

Anote a **versão declarada** de cada uma (ex.: `Flask 3.1.1`, `Express ^4.18.2`).
Sinalize dependências **declaradas mas não importadas** em nenhum arquivo (código morto de
dependência) e **importadas mas não declaradas** (dependência implícita/stdlib).

## 3. Detecção de banco de dados e entidades

Procure por:

- **ORM:** classes que herdam de `db.Model` / `Base` (SQLAlchemy), `mongoose.Schema`,
  `sequelize.define`, entidades Prisma. As tabelas/entidades são essas classes.
- **SQL cru:** `CREATE TABLE ...` em strings, chamadas `cursor.execute(...)`,
  `db.run/all/get(...)`. As tabelas são os nomes nos `CREATE TABLE`/`INSERT INTO`.
- **Connection string / arquivo:** `sqlite:///x.db`, `:memory:`, `postgres://...`,
  variáveis de ambiente de DB.

Liste as entidades/tabelas e as relações (foreign keys, `relationship`, `ForeignKey`).

## 4. Mapeamento da arquitetura atual

Classifique o nível de organização — isso muda a estratégia da Fase 3:

- **Monólito plano:** tudo em 1–4 arquivos, sem pastas por camada (ex.: `app.py` +
  `models.py` + `controllers.py`). Refatoração = criar camadas do zero.
- **God Class/God File:** uma única classe/arquivo concentra DB + rotas + lógica
  (ex.: um `AppManager` que faz tudo). Refatoração = quebrar por responsabilidade.
- **Parcialmente em camadas:** já existem pastas (`models/`, `routes/`, `services/`,
  `utils/`) mas com vazamento de responsabilidades (lógica na rota, sem controller/service
  real). Refatoração = corrigir os vazamentos e completar as camadas faltantes, **sem
  recriar o que já está certo**.

Para cada arquivo, descreva em uma linha o que ele realmente faz hoje (não o que o nome
sugere). Registre onde as responsabilidades estão misturadas.

## 5. Inventário de endpoints

Extraia **todos** os endpoints (método + path + handler), pois eles são o contrato a
preservar na Fase 3.

- **Flask:** `@app.route(...)`, `@bp.route(...)`, `app.add_url_rule(path, name, fn, methods=[...])`.
  Atenção: um mesmo path pode ter vários métodos registrados em linhas diferentes.
- **Express:** `app.get/post/put/delete(...)`, `router.<verb>(...)`, `app.use(...)`.
  Confirme com arquivos `*.http`/`*.rest`, Postman collections ou READMEs quando existirem.
- **Outros:** anotações de controller (`@GetMapping`, etc.), arquivos de rotas.

## 6. Métricas

- Número de arquivos de código analisados (exclua manifestos e assets).
- Linhas de código aproximadas (pode somar por arquivo).
- Conte entidades/tabelas e endpoints.

## Saída da fase

Use esses dados para preencher o bloco `PHASE 1: PROJECT ANALYSIS` definido no `SKILL.md`.
Seja específico: "Monolítica — tudo em 4 arquivos, sem separação de camadas" é melhor que
"desorganizada".
