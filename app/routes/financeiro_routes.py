from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import get_db_connection
from datetime import datetime
import calendar

financeiro_routes = Blueprint('financeiro_routes', __name__)

@financeiro_routes.route('/financeiro/<int:usuario_id>', methods=['GET'])
def financeiro(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  
    
    cursor.execute('SELECT * FROM financeiro WHERE usuario_id = %s ORDER BY data_pagamento', (usuario_id,))
    financeiro = cursor.fetchall()  
    
    cursor.execute('SELECT nome, id  FROM usuarios WHERE id = %s', (usuario_id,))
    usuario = cursor.fetchone()  
    
    cursor.close()
    conn.close()
    
    if usuario is None:
        flash("Usuário não encontrado.")
        return redirect(url_for('auth_routes.login'))

    return render_template('financeiro.html', financeiro=financeiro, usuario=usuario, usuario_id=usuario_id)


@financeiro_routes.route('/financeiro/cadastrar/<int:usuario_id>', methods=['GET', 'POST'])
def cadastrar_financeiro(usuario_id):
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT nome, telefone, id FROM usuarios WHERE id = %s', (usuario_id,))
    usuario = cursor.fetchone()
    
    if request.method == 'POST':
        nome = usuario['nome']
        telefone = usuario['telefone']
        valor = float(request.form['valor'])  
        meses_contratados = int(request.form['meses_contratados'])  
        data_inicio = request.form['data_pagamento']
        status = request.form['status']
        observacao = request.form['observacao']
        print(f"Status recebido: {status}")
        
        pagamentos = gerar_pagamentos(data_inicio, valor, meses_contratados)
        
        for pagamento in pagamentos:
            cursor.execute('''INSERT INTO financeiro 
                (nome, telefone, data_pagamento, status, observacao, valor, meses_contratados, usuario_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', 
                (nome, telefone, pagamento['data_pagamento'], pagamento['status'], observacao, pagamento['valor'], meses_contratados, usuario_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Pagamentos cadastrados: {pagamentos}")
        flash('Dados financeiros cadastrados com sucesso!', 'success')
        return redirect(url_for('financeiro_routes.financeiro', usuario_id=usuario_id))

    return render_template('cadastrar_financeiro.html', usuario=usuario, usuario_id=usuario_id)



def gerar_pagamentos(data_inicio, valor, meses_contratados):
    pagamentos = []
    
    try:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')  
    except ValueError as e:
        raise ValueError(f"Formato de data inválido: {e}")
    
    for i in range(meses_contratados):
        if i > 0:
            mes = data_inicio.month + i
            ano = data_inicio.year + (mes - 1) // 12
            mes = (mes - 1) % 12 + 1
            dia = data_inicio.day
            try:
                data_pagamento = datetime(ano, mes, dia)
            except ValueError:  
                data_pagamento = datetime(ano, mes, calendar.monthrange(ano, mes)[1])
        else:
            data_pagamento = data_inicio
        
        
        status = request.form['status']

        if status == "Pago": 
             pass 

        if data_pagamento < datetime.now():
            status = "Atrasado"

        elif data_pagamento >= datetime.now():
            status = "Pendente"

        pagamentos.append({
            "data_pagamento": data_pagamento.strftime('%y/%m/%d'),
            "valor": float(valor), 
            "status": status
        })
    
    return pagamentos


@financeiro_routes.route('/gerar_pagamentos', methods=['POST'])
def gerar_pagamentos_route():
    nome = request.form['nome']
    data_inicio = request.form['data_inicio']
    valor = (request.form['valor'])
    meses_contratados = (request.form['meses_contratados'])
    
    pagamentos = gerar_pagamentos(data_inicio, valor, meses_contratados)
    
    return render_template('pagamentos.html', pagamentos=pagamentos)


@financeiro_routes.route('/excluir_financeiro/<int:usuario_id>/<int:id>', methods=['POST'])
def excluir_financeiro(usuario_id, id):
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT nome FROM usuarios WHERE id = %s', (usuario_id,))
        usuario = cursor.fetchone()
        
        if usuario is None:
            flash('Usuário não encontrado!', 'error')
            return redirect(url_for('financeiro_routes.financeiro', usuario_id=usuario_id))

        cursor.execute('DELETE FROM financeiro WHERE id = %s', (id,))
        conn.commit()

        flash('Pagamento excluído com sucesso!', 'success')
        return redirect(url_for('financeiro_routes.financeiro', usuario_id=usuario_id, usuario=usuario))

    except Exception as e:
        flash(f'Erro ao excluir pagamento: {e}', 'error')
        return redirect(url_for('financeiro_routes.financeiro', usuario_id=usuario_id, usuario=usuario))







