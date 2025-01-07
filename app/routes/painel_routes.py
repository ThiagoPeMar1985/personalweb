from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from app.database import get_db_connection
from datetime import datetime
import mysql.connector  


painel_routes = Blueprint('painel_routes', __name__)

@painel_routes.route('/painel_financeiro', methods=['GET'])
def painel_controle():
    usuario_id = request.args.get('usuario_id')
    ano = datetime.now().year
    mes = datetime.now().month
    meses = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    nome_mes = f"{meses[mes - 1].capitalize()} de {ano}" 
    contas = mostrar_contas(mes, ano)
    entrada_valores = mostrar_valores(mes, ano)
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)

        cursor.execute("SELECT id, nome FROM usuarios")
        usuarios = cursor.fetchall()
        
        print(f"usuario_id: {usuario_id}")
        
        if usuario_id:
            cursor.execute("""
                SELECT * FROM financeiro WHERE usuario_id = %s """, (usuario_id,))
            financeiro = cursor.fetchall()
            
        else:
            financeiro = []

    except mysql.connector.Error as e:
        flash(f'Erro ao carregar dados financeiros: {e}', 'error')
        financeiro = []
    finally:
        cursor.close()
        cnx.close()

    return render_template('painelfinanceiro.html', 
        usuarios=usuarios, 
        usuario_id=usuario_id, 
        financeiro=financeiro, 
        nome_mes=nome_mes, 
        contas=contas, 
        entrada_valores=entrada_valores
    )

@painel_routes.route('/contas', methods=['GET'])
def mostrar_contas():
    mes = request.args.get('mes', datetime.now().month)
    ano = request.args.get('ano', datetime.now().year)
    
    try:
        
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)

        
        cursor.execute("""
            SELECT descricao, valor, data_vencimento, status
            FROM contas
            WHERE MONTH(data_vencimento) = %s
            AND YEAR(data_vencimento) = %s
        """, (mes, ano))
        
        
        contas = cursor.fetchall()
        
        
        total_contas = sum(c['valor'] for c in contas)
        
    except mysql.connector.Error as e:
        flash(f'Erro ao carregar as contas: {e}', 'error')
        contas = []
        total_contas = 0
        print(f"Erro ao acessar o banco de dados: {e}")
    finally:
        cursor.close()
        cnx.close()
    
    
    return render_template('painelfinanceiro.html', contas=contas, total_contas=total_contas, mes=mes, ano=ano)

def mostrar_contas(mes, ano):
    

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)

        
        cursor.execute("""
            SELECT descricao, valor, data_vencimento, status
            FROM contas
            WHERE MONTH(data_vencimento) = %s
            AND YEAR(data_vencimento) = %s
        """, (mes, ano))
        
        contas = cursor.fetchall()

        total_contas = sum(c['valor'] for c in contas)

    except mysql.connector.Error as e:
        flash(f'Erro ao carregar as contas: {e}', 'error')
        contas = []
        total_contas = 0
        print(f"Erro ao acessar o banco de dados: {e}")
    finally:
        cursor.close()
        cnx.close()

    return contas

def mostrar_valores(mes, ano):
    """Fetch financial entries for the given month and year."""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT v.usuario_id, u.nome, v.data_pagamento, v.valor_pago
            FROM valores v
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE MONTH(v.data_pagamento) = %s
            AND YEAR(v.data_pagamento) = %s
            ORDER BY v.data_pagamento DESC
        """, (mes, ano))
        
        entrada_valores = cursor.fetchall()
        return entrada_valores
        
    except mysql.connector.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        return []
    
    finally:
        cursor.close()
        cnx.close()

@painel_routes.route('/lancar_contas', methods=['GET', 'POST'])
def lancar_contas():
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = request.form['valor']
        data_vencimento = request.form['data_vencimento']
        status = request.form['status']

        try:
            cnx = get_db_connection()
            cursor = cnx.cursor(dictionary=True)

            # Inserir a nova conta no banco de dados
            cursor.execute("""
                INSERT INTO contas (descricao, valor, data_vencimento, status)
                VALUES (%s, %s, %s, %s)
            """, (descricao, valor, data_vencimento, status))

            cnx.commit()
            flash('Conta lançada com sucesso!', 'success')
        except mysql.connector.Error as e:
            flash(f'Erro ao lançar conta: {e}', 'error')
        finally:
            cursor.close()
            cnx.close()

        return redirect(url_for('painel_routes.painel_controle'))

    return render_template('lancar_conta.html')


def lancar_pagamentos_em_entradas():
    
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)
        
        
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        

        cursor.execute("""
            SELECT id, usuario_id, nome, valor, data_pagamento 
            FROM financeiro 
            WHERE MONTH(data_pagamento) = %s 
            AND YEAR(data_pagamento) = %s 
            AND status = 'pago'
        """, (mes_atual, ano_atual))
        
        
        pagamentos = cursor.fetchall()
        print(f"Pagamentos encontrados: {pagamentos}")
        

        for pagamento in pagamentos:

            cursor.execute("SELECT id FROM usuarios WHERE id = %s", (pagamento['usuario_id'],))
            usuario = cursor.fetchone()
            
            if usuario:
                cursor.execute("""
                    INSERT INTO valores (usuario_id, nome, data_pagamento, valor_pago) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    pagamento['usuario_id'],  
                    pagamento['nome'], 
                    pagamento['data_pagamento'], 
                    pagamento['valor']
                ))
                
            else:
                print(f"Usuário com ID {pagamento['usuario_id']} não encontrado na tabela 'usuarios'")

        cnx.commit()
        
        print("Dados commitados")
        
    except mysql.connector.Error as e:
        
        if cnx:
            cnx.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnx' in locals():
            cnx.close()


@painel_routes.route('/financeiro/pagar/<int:id>/<int:usuario_id>', methods=['POST'])
def pagar_financeiro(id, usuario_id):
    print('foi chamado')

    try:
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        
        cursor.execute('UPDATE financeiro SET status = %s WHERE id = %s', ('pago', id))
        conn.commit()

        lancar_pagamentos_em_entradas()

        flash('Pagamento atualizado com sucesso!', 'success')

    except mysql.connector.Error as e:
        flash(f'Erro ao atualizar pagamento: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('financeiro_routes.financeiro', usuario_id=usuario_id))

@painel_routes.route('/lancar_pagamentos', methods=['GET'])
def lancar_pagamentos():
    lancar_pagamentos_em_entradas()
    return redirect(url_for('painel_routes.painel_controle'))