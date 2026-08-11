"""Camada de View/roteamento: mapeia método+path → controller. Sem lógica de negócio.

Preserva exatamente os endpoints originais (mesmos métodos e paths).
"""
from src.middlewares.auth import admin_required


def register_routes(app, produtos, usuarios, pedidos, relatorios, sistema, admin):
    # Produtos
    app.add_url_rule("/produtos", "listar_produtos", produtos.listar, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", produtos.buscar_lista, methods=["GET"])
    app.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produtos.buscar, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", produtos.criar, methods=["POST"])
    app.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produtos.atualizar, methods=["PUT"])
    app.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produtos.deletar, methods=["DELETE"])

    # Usuários
    app.add_url_rule("/usuarios", "listar_usuarios", usuarios.listar, methods=["GET"])
    app.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", usuarios.buscar, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuarios.criar, methods=["POST"])
    app.add_url_rule("/login", "login", usuarios.login, methods=["POST"])

    # Pedidos
    app.add_url_rule("/pedidos", "criar_pedido", pedidos.criar, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", pedidos.listar_todos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedidos.listar_por_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedidos.atualizar_status, methods=["PUT"])

    # Relatórios
    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorios.vendas, methods=["GET"])

    # Sistema
    app.add_url_rule("/", "index", sistema.index, methods=["GET"])
    app.add_url_rule("/health", "health_check", sistema.health, methods=["GET"])

    # Admin (protegidos por token de admin)
    app.add_url_rule("/admin/reset-db", "reset_database", admin_required(admin.reset_db), methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", admin_required(admin.query), methods=["POST"])
