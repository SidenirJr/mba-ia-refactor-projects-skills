"""Camada de View/roteamento: mapeia método+path → controller. Sem lógica de negócio.

Preserva exatamente os 19 endpoints originais (mesmos métodos e paths) e aplica a
política de autorização:

  * público      — `GET /`, `GET /health`, `POST /login`, `POST /usuarios` (cadastro) e
                   o catálogo de leitura (`GET /produtos`, `/produtos/busca`, `/produtos/<id>`);
  * autenticado  — `POST /pedidos`, `GET /pedidos/usuario/<id>`, `GET /usuarios/<id>`
                   (os dois últimos com regra de dono/admin no service);
  * admin        — escrita de produtos, listagens globais, status de pedido, relatórios;
  * admin + header `X-Admin-Token` — endpoints `/admin/*`.
"""
from src.middlewares.auth import admin_token_required


def register_routes(app, produtos, usuarios, pedidos, relatorios, sistema, admin, guards):
    login_required = guards.login_required
    admin_required = guards.admin_required

    # Produtos — catálogo de leitura público; escrita restrita a admin
    app.add_url_rule("/produtos", "listar_produtos", produtos.listar, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", produtos.buscar_lista, methods=["GET"])
    app.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produtos.buscar, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", admin_required(produtos.criar), methods=["POST"])
    app.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", admin_required(produtos.atualizar), methods=["PUT"])
    app.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", admin_required(produtos.deletar), methods=["DELETE"])

    # Usuários — cadastro e login públicos; leitura individual é do dono ou admin
    app.add_url_rule("/usuarios", "listar_usuarios", admin_required(usuarios.listar), methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", login_required(usuarios.buscar), methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuarios.criar, methods=["POST"])
    app.add_url_rule("/login", "login", usuarios.login, methods=["POST"])

    # Pedidos
    app.add_url_rule("/pedidos", "criar_pedido", login_required(pedidos.criar), methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", admin_required(pedidos.listar_todos), methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", login_required(pedidos.listar_por_usuario), methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", admin_required(pedidos.atualizar_status), methods=["PUT"])

    # Relatórios
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", admin_required(relatorios.vendas), methods=["GET"])

    # Sistema (públicos)
    app.add_url_rule("/", "index", sistema.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", sistema.health, methods=["GET"])

    # Admin — exigem o header X-Admin-Token E uma sessão de usuário admin
    app.add_url_rule("/admin/reset-db", "reset_database", admin_token_required(admin_required(admin.reset_db)), methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", admin_token_required(admin_required(admin.query)), methods=["POST"])
