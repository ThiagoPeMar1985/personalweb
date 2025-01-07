# app/database.py

import mysql.connector

config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Beer1234',
    'database': 'personalweb'
}

def get_db_connection():
    return mysql.connector.connect(**config)
    

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

if __name__ == '__main__':
    server = Server(app.wsgi)
    server.serve(port=5000)  # Porta do Flask
