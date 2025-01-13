from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import get_db_connection
from datetime import datetime, timedelta
import re

agenda_routes = Blueprint('agenda_routes', __name__)

def obter_agenda(usuario_id):
    agenda = []  
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        today = datetime.today().date()
        start_of_week = today - timedelta(days=today.weekday())  
        end_of_week = start_of_week + timedelta(days=6)  

        start_of_week_str = start_of_week.strftime('%Y-%m-%d')
        end_of_week_str = end_of_week.strftime('%Y-%m-%d')

        query = """
            SELECT 
                a.id,  
                a.usuario_id, 
                a.data, 
                a.duracao, 
                a.horario,  
                a.descricao, 
                u.nome AS aluno,
                a.tipo AS tipo,
                DAYNAME(a.data) AS dia_semana 
            FROM agenda a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.data BETWEEN %s AND %s AND a.data >= %s  
            ORDER BY a.horario ASC
        """

        cursor.execute(query, (start_of_week_str, end_of_week_str, today))
        agenda = cursor.fetchall()

       
        for agendamento in agenda:
            usuario_id = agendamento['usuario_id']
            agendamento_id = agendamento['id']  
            horario_str = agendamento['horario']
            duracao_str = agendamento['duracao']
            agendamento['horario_final'] = calcular_horario_final_com_busca(agendamento_id)

    except Exception as e:
        print(f'Erro ao obter agenda: {e}')
    finally:
        cursor.close() if cursor else None
        conn.close() if conn else None
   
    return agenda


def buscar_agenda():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM agenda"
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    return resultados  


@agenda_routes.route('/agenda', methods=['GET'])
def agenda():
    resultados = buscar_agenda()  
    agenda = obter_agenda(resultados)

    dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]  
    dias_semana_traduzidos = {
        "Monday": "Segunda", 
        "Tuesday": "Terça", 
        "Wednesday": "Quarta", 
        "Thursday": "Quinta", 
        "Friday": "Sexta", 
        "Saturday": "Sábado", 
        "Sunday": "Domingo"
    }

  
    return render_template('agenda.html', agenda=agenda, dias=dias, dias_semana_traduzidos=dias_semana_traduzidos,resultados=resultados)



@agenda_routes.route('/agenda/criar', methods=['GET', 'POST'])
def criar_agenda():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, nome FROM usuarios")
    usuarios = cursor.fetchall()

    dias_da_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

    horarios = []
    for hour in range(5, 24):
        for minute in range(0, 60, 10):
            horario = f"{hour:02}:{minute:02}"
            horarios.append(horario)

    if request.method == 'POST':
        usuario_id = request.form['usuario_id']
        data = request.form['data']
        horario = request.form['horario']
        duracao = request.form['duracao']
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        repetir = 'repetir' in request.form  

        if not data or not re.match(r'\d{4}-\d{2}-\d{2}', data):
            return render_template('criar_agenda.html', error_message='Data inválida. Use o formato YYYY-MM-DD.', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)

        data_datetime = datetime.strptime(data, "%Y-%m-%d").date()
        if data_datetime < datetime.today().date():
            return render_template('criar_agenda.html', error_message='Não é possível agendar para uma data anterior ao dia atual.', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)

        agendamento_id_atual = None
        if verificar_sobreposicao_agendamento(data, horario, duracao, agendamento_id_atual):
            return render_template('criar_agenda.html', error_message='Já existe um agendamento para este dia e horário.', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)

        try:
            duracao_horas, duracao_minutos = map(int, duracao.split(':'))
        except ValueError:
            return render_template('criar_agenda.html', error_message='Duração inválida. Use o formato HH:MM.', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)

        duracao = timedelta(hours=duracao_horas, minutes=duracao_minutos)

        try:
            horario_datetime = datetime.strptime(horario, '%H:%M')
        except ValueError:
            return render_template('criar_agenda.html', error_message='Horário inválido. Use o formato HH:MM.', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)

        horario_final = horario_datetime + duracao
        criar_agenda(usuario_id, data_datetime.strftime("%Y-%m-%d"), duracao, tipo, descricao, horario)

        if repetir:
            data_fim_repeticao = request.form['data_fim_repeticao']  # Coloque a data de término da repetição aqui
            data_fim_repeticao = datetime.strptime(data_fim_repeticao, "%Y-%m-%d").date()

            while data_datetime <= data_fim_repeticao:
                data_nova = data_datetime + timedelta(weeks=1)  # Repete a cada semana
                if data_nova <= data_fim_repeticao:
                    criar_agenda(usuario_id, data_nova.strftime("%Y-%m-%d"), duracao, tipo, descricao, horario)
                data_datetime = data_nova  

        cursor.close()
        connection.close()

        return redirect(url_for('agenda_routes.agenda'))

    cursor.close()
    connection.close()

    return render_template('criar_agenda.html', usuarios=usuarios, horarios=horarios, dias_da_semana=dias_da_semana)


def completar_dia_semana(data):
    data_obj = datetime.strptime(data, '%Y-%m-%d') 
    return data_obj.strftime('%A')  


def criar_agenda(usuario_id, data, duracao, tipo, descricao, horario):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if isinstance(duracao, timedelta):
            duracao_horas = duracao.seconds // 3600
            duracao_minutos = (duracao.seconds % 3600) // 60
            duracao = f"{duracao_horas:02}:{duracao_minutos:02}"

        dia_semana = completar_dia_semana(data)
  
        query_check = """
            SELECT COUNT(*) FROM agenda 
            WHERE data = %s AND horario = %s
        """
        cursor.execute(query_check, (data, horario))
        count = cursor.fetchone()[0]
        
        if count > 0:
            return render_template('criar_agenda.html', error_message='Já existe um agendamento para este dia e horário.')
        
        query = """
            INSERT INTO agenda (usuario_id, data, duracao, tipo, descricao, horario, dia_semana)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (usuario_id, data, duracao, tipo, descricao, horario, dia_semana))

        conn.commit()
        
    except Exception as e:
        print(f'Erro ao criar cadastro: {e}')  
    finally:
        cursor.close() if cursor else None
        conn.close() if conn else None



def buscar_horario(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT horario FROM agenda WHERE usuario_id = %s AND horario != '00:00'"  
    cursor.execute(query, (usuario_id,))
    resultado = cursor.fetchone()
    
    if resultado and resultado[0]:
        return str(resultado[0])  

   
    return None  


def buscar_duracao(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT duracao FROM agenda WHERE usuario_id = %s LIMIT 1", (usuario_id,))  
    resultado = cursor.fetchone()
    conn.close()
    if resultado and 'duracao' in resultado:
        return (resultado['duracao']) 
    return 0  


def buscar_agendamento_por_id(agendamento_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM agenda WHERE id = %s", (agendamento_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def calcular_horario_final_com_busca(agendamento_id):
    agendamento = buscar_agendamento_por_id(agendamento_id)

    horario_str = agendamento['horario']
    duracao_str = agendamento['duracao']


    try:
        horario = datetime.strptime(horario_str, "%H:%M")
    except ValueError:
        raise ValueError(f"Horário inválido: {horario_str}")

   
    duracao_horas, duracao_minutos = map(int, duracao_str.split(":"))
    duracao = timedelta(hours=duracao_horas, minutes=duracao_minutos)


    horario_final = horario + duracao
    return horario_final.strftime("%H:%M")


def obter_agenda_usuario(usuario_id):
    agenda = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                a.id,
                a.usuario_id, 
                a.data, 
                a.duracao, 
                a.horario,  
                a.descricao, 
                u.nome AS aluno,
                a.tipo AS tipo,
                DAYNAME(a.data) AS dia_semana 
            FROM agenda a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.usuario_id = %s
            ORDER BY a.horario ASC
        """
        cursor.execute(query, (usuario_id,))
        agenda = cursor.fetchall()
        for agendamento in agenda:
            agendamento['horario_final'] = calcular_horario_final_com_busca(agendamento['id']) 
    except Exception as e:
        print(f'Erro ao obter agenda: {e}')
    finally:
        cursor.close() if cursor else None
        conn.close() if conn else None
        
    return agenda


@agenda_routes.route('/agenda/excluir/<int:id>', methods=['POST'])
def excluir_agendamento(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM agenda WHERE id = %s", (id,))
        connection.commit()
        flash('Agendamento excluído com sucesso!', 'success')
    except Exception as e:
        flash('Erro ao excluir agendamento.', 'danger')
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for('agenda_routes.agenda'))


@agenda_routes.route('/agenda/editar/<int:id>', methods=['GET', 'POST'])
def editar_agendamento(id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM agenda WHERE id = %s", (id,))
    agendamento = cursor.fetchone()

    horarios1 = []
    for hour in range(5, 24): 
        for minute in range(0, 60, 10): 
            horario = f"{hour:02}:{minute:02}"
            horarios1.append(horario)   

    if request.method == 'POST':
        data = request.form['data']
        horario = request.form['horario']
        duracao = request.form['duracao']
        tipo = request.form['tipo']
        descricao = request.form['descricao']

        if verificar_sobreposicao_agendamento(data, horario, duracao, id):
            return render_template('editar_agenda.html', error_message='Já existe um agendamento para este dia e horário.', horarios1=horarios1, agendamento=agendamento)

        cursor.execute("UPDATE agenda SET data = %s, horario = %s, duracao = %s, tipo = %s, descricao = %s WHERE id = %s", (data, horario, duracao, tipo, descricao, id))
        connection.commit()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('agenda_routes.agenda'))
    
    return render_template('editar_agenda.html', agendamento=agendamento, horarios1=horarios1)



from datetime import datetime, timedelta

def verificar_sobreposicao_agendamento(data, horario, duracao, agendamento_id_atual=None):
    print("entrou aqui ", data, horario, duracao, agendamento_id_atual)
    conn = get_db_connection()
    cursor = conn.cursor()

    duracao_horas, duracao_minutos = map(int, duracao.split(':'))
    duracao_timedelta = timedelta(hours=duracao_horas, minutes=duracao_minutos)

    horario_datetime = datetime.strptime(horario, '%H:%M')
    horario_final = horario_datetime + duracao_timedelta

    if agendamento_id_atual is None:
        query = """
            SELECT id, horario, duracao FROM agenda
            WHERE data = %s
        """
        cursor.execute(query, (data,))
    else:
        query = """
            SELECT id, horario, duracao FROM agenda
            WHERE data = %s AND id != %s
        """
        cursor.execute(query, (data, agendamento_id_atual))
    
    agendamentos_existentes = cursor.fetchall()

    for agendamento in agendamentos_existentes:
        agendamento_horario = agendamento[1]
        agendamento_duracao = agendamento[2]

        agendamento_horario_datetime = datetime.strptime(agendamento_horario, '%H:%M')
        agendamento_duracao_horas, agendamento_duracao_minutos = map(int, agendamento_duracao.split(':'))
        agendamento_duracao_timedelta = timedelta(hours=agendamento_duracao_horas, minutes=agendamento_duracao_minutos)
        agendamento_horario_final = agendamento_horario_datetime + agendamento_duracao_timedelta

        if (horario_datetime < agendamento_horario_final and horario_final > agendamento_horario_datetime):
            cursor.close()
            conn.close()
            return True  

    cursor.close()
    conn.close()
    return False