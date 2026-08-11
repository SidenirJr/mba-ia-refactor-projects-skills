# 04 — Guidelines de Arquitetura MVC (Fase 3)

O alvo é uma arquitetura **MVC em camadas**, com responsabilidades claras e dependências
fluindo em uma só direção:

```
Request → Routes (View) → Controller → Service → Model/Repository → DB
                                   ↑ Middlewares (erro, auth, validação) ↑
                              Config (segredos/ambiente)  •  composition root (entrypoint)
```

## Responsabilidade de cada camada

### Config
- Centraliza segredos e parâmetros por ambiente, **lidos de variáveis de ambiente** (`.env`
  + loader; nunca hardcoded). Ex.: `SECRET_KEY`, `DEBUG`, caminho/URL do banco, chaves de
  terceiros, credenciais SMTP/gateway, token de admin.
- Um único lugar para `DEBUG` — desligado por padrão, ligado só via env em dev.

### Models / Repositories (a camada "M")
- **Model:** representa a entidade (campos, relações) e regras invariantes simples.
- **Repository:** encapsula **todo** acesso a dados de uma entidade (CRUD + queries). É aqui
  que vivem as queries — **sempre parametrizadas**. Nenhuma outra camada escreve SQL.
- Sem regra de negócio de orquestração aqui (isso é do service). Sem lógica HTTP.

### Views / Routes (a camada "V" em APIs)
- Em uma API REST, a "View" é a camada de **roteamento + serialização** da resposta.
- Mapeia método+path → controller. Nada de lógica de negócio nem acesso a dados.
- Em Flask: Blueprints. Em Express: `Router` por recurso.

### Controllers (a camada "C")
- **Finos.** Traduzem HTTP ↔ domínio: leem request, validam entrada (ou delegam ao schema),
  chamam **um** service, formatam a resposta e o status. Não acessam o DB diretamente.

### Services
- **Lógica de negócio.** Orquestram repositories, aplicam regras (total/estoque, descontos,
  overdue, checkout, hashing de senha, decisão de pagamento via abstração), controlam
  **transações**. Não conhecem `request`/`response` HTTP.

### Middlewares
- Transversais: **error handler central** (uma resposta de erro padronizada, sem vazar
  stack), **auth/authorization guard** (protege endpoints sensíveis), validação, CORS
  restritivo, logging.

### Composition root (entrypoint)
- `app.py`/`app.js`: cria a aplicação, lê config, registra middlewares e rotas, conecta as
  dependências (injeção) e sobe o servidor. **Sem regra de negócio nem SQL.**

## Regras de ouro

1. **Dependências apontam para dentro:** routes→controllers→services→repositories. Camada de
   baixo nunca importa camada de cima.
2. **Uma responsabilidade por arquivo.** Se um arquivo "faz e também faz", divida.
3. **Injeção de dependência:** services recebem repositories; repositories recebem a conexão.
   Isso permite testar com fakes.
4. **Segredos e config só na camada Config.** Código de domínio lê config, não literais.
5. **Serialização não vaza dados sensíveis:** o objeto de resposta nunca inclui senha/hash/
   segredo. Use DTO/schema ou um `to_dict` que omite campos sensíveis.
6. **Preserve o contrato:** os paths e métodos do inventário da Fase 1 continuam existindo.

## Árvore-alvo de referência

Adapte os nomes à convenção da stack; o que importa são as camadas.

```
src/
├── config/                 # settings/env
├── models/                 # entidades + repositories (acesso a dados parametrizado)
├── views/  (ou routes/)    # roteamento + serialização
├── controllers/            # handlers finos por recurso
├── services/               # regras de negócio + transações
├── middlewares/            # error handler, auth guard, validação
└── app.(py|js)             # composition root / entrypoint
```

## Mapa de tradução entre stacks (agnosticismo)

| Conceito MVC | Python/Flask | Node/Express |
|---|---|---|
| Entrypoint/composition root | `app.py` com app-factory `create_app()` | `app.js` que monta o `express()` |
| Roteamento (View) | Blueprint (`Blueprint`, `@bp.route`) | `express.Router()` por recurso |
| Controller | função/módulo por recurso | função/módulo por recurso |
| Service | classe/módulo de serviço | classe/módulo de serviço |
| Repository/Model | classe ORM + repo, ou módulo com SQL parametrizado | classe repo com SQL parametrizado/ORM |
| Config | módulo `config` + `python-dotenv` | módulo `config` + `dotenv` |
| Error handler | `@app.errorhandler` / handler central | middleware `(err, req, res, next)` |
| Auth guard | decorator/`before_request` | middleware |
| Hash de senha | `werkzeug.security` / `bcrypt` | `bcrypt` / `crypto.scrypt` |

## Adaptação ao nível de organização

- **Monólito plano / God Class:** crie todas as camadas; mova o código para o lugar certo.
- **Parcialmente em camadas:** **não recrie o que já está correto.** Introduza as camadas
  faltantes (tipicamente controllers + services), mova a lógica das rotas para os services,
  reutilize helpers/constantes/métodos já existentes, e corrija vazamentos. Preserve a
  organização boa que já houver.
