from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from app.database import get_db_connection
import mysql.connector  
from .auth_routes import verificar_acesso

menu_routes = Blueprint('menu_routes', __name__)

@menu_routes.route('/menu')
@verificar_acesso
def menu():
    if 'username' not in session:  
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('auth_routes.index'))  


    try:
        cnx = get_db_connection()  
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, username, tipo  FROM usuarios")  
        usuarios = cursor.fetchall()  
        
        cursor.close()
        cnx.close()  
        
    except mysql.connector.Error as e:
        flash(f'Erro ao buscar usuários: {e}', 'error')  
        usuarios = []  

    return render_template('menu.html', usuarios=usuarios)  

