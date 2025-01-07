# app/__init__.py

from flask import Flask
from .routes.auth_routes import auth_routes
from .routes.menu_routes import menu_routes
from .routes.aluno_routes import aluno_routes
from .routes.admin_routes import admin_routes
from .routes.financeiro_routes import financeiro_routes
from .routes.painel_routes import painel_routes

from .database import get_db_connection

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Periard'

    # Registrar Blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(menu_routes)
    app.register_blueprint(aluno_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(financeiro_routes)
    app.register_blueprint(painel_routes)

    return app