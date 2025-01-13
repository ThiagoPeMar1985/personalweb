
from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from app.database import get_db_connection
from .auth_routes import verificar_acesso

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/criar_usuario', methods=['GET', 'POST'])
@verificar_acesso
def criar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        username = request.form['username']
        senha = request.form['senha']
        tipo = request.form['tipo']
        telefone = request.form['telefone']

        try:
            cnx = get_db_connection()
            cursor = cnx.cursor()
            query = "INSERT INTO usuarios (nome, username, senha, tipo,telefone ) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (nome, username, senha, tipo, telefone))
            cnx.commit()
            cursor.close()
            cnx.close()

            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('menu_routes.menu'))

        except mysql.connector.Error as e:
            flash(f'Erro ao criar usuário: {e}', 'error')

    return render_template('criar_usuario.html')
@admin_routes.route('/usuarios')
def listar_usuarios():
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, username, tipo FROM usuarios")
        usuarios = cursor.fetchall()
    except mysql.connector.Error as e:
        flash(f'Erro ao buscar usuários: {e}', 'error')
        usuarios = []
    finally:
        cursor.close()
        cnx.close()
    
    return render_template('menu.html', usuarios=usuarios)

@admin_routes.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if request.method == 'POST':
        nome = request.form['nome']
        username = request.form['username']
        senha = request.form['senha']
        tipo = request.form['tipo']
        telefone = request.form['telefone']

        try:
            cnx = get_db_connection()
            cursor = cnx.cursor()
            query = """
                UPDATE usuarios 
                SET nome = %s, username = %s, senha = %s, tipo = %s,  telefone = %s
                WHERE id = %s
            """
            cursor.execute(query, (nome, username, senha, tipo, telefone, id))
            cnx.commit()
            cursor.close()
            cnx.close()

            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin_routes.listar_usuarios'))

        except mysql.connector.Error as e:
            flash(f'Erro ao atualizar usuário: {e}', 'error')

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    cnx.close()

    if usuario is None:
        flash('Usuário não encontrado', 'error')
        return redirect(url_for('admin_routes.listar_usuarios'))

    return render_template('editar_usuario.html', usuario=usuario)

@admin_routes.route('/usuarios/excluir/<int:id>', methods=['POST'])
def excluir_usuario(id):
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        query = "DELETE FROM usuarios WHERE id = %s"
        cursor.execute(query, (id,))
        cnx.commit()
        cursor.close()
        cnx.close()
        flash('Usuário excluído com sucesso!', 'success')
    except mysql.connector.Error as e:
        flash(f'Erro ao excluir usuário: {e}', 'error')
    
    return redirect(url_for('admin_routes.listar_usuarios'))

