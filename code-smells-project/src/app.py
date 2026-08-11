"""Composition root: cria a app, lê config, conecta as dependências (DI) e registra rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.controllers.admin_controller import AdminController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.system_controller import SystemController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import register_error_handlers
from src.models import database
from src.models.pedido_repository import PedidoRepository
from src.models.produto_repository import ProdutoRepository
from src.models.usuario_repository import UsuarioRepository
from src.services.notification_service import NotificationService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService
from src.views.routes import register_routes


def create_app():
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    # Infraestrutura de banco
    database.init_app(app)
    with app.app_context():
        database.init_db()
    get_db = database.get_db

    # Camada de dados (repositories recebem o provedor de conexão — injeção de dependência)
    produto_repo = ProdutoRepository(get_db)
    usuario_repo = UsuarioRepository(get_db)
    pedido_repo = PedidoRepository(get_db)

    # Camada de serviços (regras de negócio)
    notification_service = NotificationService()
    produto_service = ProdutoService(produto_repo)
    usuario_service = UsuarioService(usuario_repo)
    pedido_service = PedidoService(pedido_repo, produto_repo, notification_service)
    relatorio_service = RelatorioService(pedido_repo)

    # Controllers (HTTP fino)
    produtos = ProdutoController(produto_service)
    usuarios = UsuarioController(usuario_service)
    pedidos = PedidoController(pedido_service)
    relatorios = RelatorioController(relatorio_service)
    sistema = SystemController(get_db)
    admin = AdminController(get_db)

    register_routes(app, produtos, usuarios, pedidos, relatorios, sistema, admin)
    register_error_handlers(app)
    return app
