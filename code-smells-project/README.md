# code-smells-project

API de E-commerce em Python/Flask. Originalmente um monólito de 4 arquivos com code smells
intencionais; **refatorado para MVC em camadas** pela skill `refactor-arch`.

## Como rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # ajuste os valores (opcional em dev)
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas **hasheadas**).

## Estrutura (MVC)

```
app.py                       # entry point (python app.py) — também é o objeto WSGI
src/
├── app.py                   # composition root (app-factory + injeção de dependência)
├── config/settings.py       # configuração por ambiente (sem segredos hardcoded)
├── models/                  # repositories com queries parametrizadas + schema/seed
│   ├── database.py
│   ├── produto_repository.py
│   ├── usuario_repository.py
│   └── pedido_repository.py
├── services/                # regras de negócio (validação, total/estoque, descontos, auth)
├── controllers/             # handlers HTTP finos
├── views/routes.py          # roteamento (preserva os endpoints originais)
├── middlewares/             # error handler central + admin guard
└── errors.py                # exceções de domínio
```

## Variáveis de ambiente

Veja `.env.example`. Em produção, defina `SECRET_KEY`, `ADMIN_TOKEN` e `DEBUG=false`.
Os endpoints `/admin/*` exigem o header `X-Admin-Token: <ADMIN_TOKEN>`.
