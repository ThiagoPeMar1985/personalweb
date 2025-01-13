# app/routes/auth_routes.py

from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from functools import wraps
from app.database import get_db_connection

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/')
def index():
    return render_template('login.html')

@auth_routes.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    query = "SELECT * FROM usuarios WHERE username = %s AND senha = %s"
    cursor.execute(query, (username, password))
    results = cursor.fetchall()
    cursor.close()
    cnx.close()

    if results:
        user = results[0]
        session['username'] = username
        session['user_id'] = user['id']
        session['user_tipo'] = user['tipo']

        if user['tipo'] == 'adm':
            return redirect(url_for('menu_routes.menu'))  
        elif user['tipo'] in ['aluno', 'visit']:
            return redirect(url_for('aluno_routes.alunos'))
        else:
            flash('Tipo de usuário desconhecido', 'error')
            return redirect(url_for('auth_routes.index'))
    else:
        flash('Usuário ou senha inválidos!', 'error')
        return redirect(url_for('auth_routes.index'))

@auth_routes.route('/logout')
def logout():
    session.clear()  
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('auth_routes.index')) 

def verificar_acesso(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        usuario = session.get('usuario')
        if usuario and usuario['tipo'] in ['aluno', 'visitante']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('aluno_routes.alunos'))  
        return func(*args, **kwargs)
    return wrapper