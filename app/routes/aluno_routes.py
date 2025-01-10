from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from app.database import get_db_connection
from .agenda_routes import obter_agenda_usuario , calcular_horario_final_com_busca, buscar_duracao
from datetime import datetime

aluno_routes = Blueprint('aluno_routes', __name__)

@aluno_routes.route('/alunos', methods=['GET'])
def alunos():
    if 'username' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('auth_routes.index'))

    username = session.get('username')
    nome = None
    avaliacoes = []
    treinos = []
    usuario_id = None
    usuario = None  
    agenda = []
    

    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True)

        if username:
            query_usuario = "SELECT * FROM usuarios WHERE username = %s"
            cursor.execute(query_usuario, (username,))
            usuario = cursor.fetchone()
            
            if usuario:
                usuario_id = usuario['id']
                nome = usuario['nome'] 

                query_aluno = "SELECT * FROM alunos WHERE usuario_id = %s"
                cursor.execute(query_aluno, (usuario_id,))
                avaliacoes = cursor.fetchall()

                query_treinos = "SELECT * FROM treinos WHERE usuario_id = %s"
                cursor.execute(query_treinos, (usuario_id,))
                treinos = cursor.fetchall()

                agenda = obter_agenda_usuario(usuario_id)

                if agenda: 
                    agenda = [agendamento for agendamento in agenda if 'data' in agendamento and agendamento['data'] >= datetime.now().date()]
                    agenda = sorted(agenda, key=lambda x: x['horario'])
                else:
                    print("Nenhum agendamento encontrado.")
                    
                for agendamento in agenda:
                    agendamento['horario_final'] = calcular_horario_final_com_busca(usuario_id)
                    agendamento['duracao'] = buscar_duracao(agendamento['id'])
                    
                return render_template('alunos.html', usuario_id=usuario_id, agenda=agenda, nome=nome, avaliacoes=avaliacoes, treinos=treinos,usuario=usuario)


            else:
                flash("Usuário não encontrado.", "error")
        else:
            flash("Nome do aluno não informado. Exibindo todas as avaliações.", "info")
            query_todos_alunos = "SELECT * FROM alunos"
            cursor.execute(query_todos_alunos)
            avaliacoes = cursor.fetchall()

        cursor.close()
        cnx.close()
    except Exception as e:
        flash(f"Erro ao acessar o banco de dados: {e}", "error")
   
    
    return render_template('alunos.html', nome=nome, usuario_id=usuario_id, avaliacoes=avaliacoes, treinos=treinos,usuario=usuario, agenda=agenda,)

@aluno_routes.route('/cadastro_aluno/<int:usuario_id>/<nome>', methods=['GET', 'POST'])
def cadastro_aluno(usuario_id, nome):
   
    cnx = get_db_connection()
    cursor = cnx.cursor()

  
    if request.method == 'POST':
        
        idade = request.form['idade']
        altura = request.form['altura']
        peso = request.form['peso']
        imc = request.form['imc']
        porcentagem_gordura = request.form['porcentagem_gordura']
        porcentagem_musculo = request.form['porcentagem_musculo']
        taxa_metabolica_basal = request.form['taxa_metabolica_basal']
        idade_media = request.form['idade_media']
        gordura_visceral = request.form['gordura_visceral']
        pescoco = request.form['pescoco']
        ombro = request.form['ombro']
        torax = request.form['torax']
        cintura = request.form['cintura']
        abdominal = request.form['abdominal']
        quadril = request.form['quadril']
        braco_direito = request.form['braco_direito']
        braco_esquerdo = request.form['braco_esquerdo']
        braco_circulo_direito = request.form['braco_circulo_direito']
        braco_circulo_esquerdo = request.form['braco_circulo_esquerdo']
        antebraco_direito = request.form['antebraco_direito']
        antebraco_esquerdo = request.form['antebraco_esquerdo']
        perna_direita = request.form['perna_direita']
        perna_esquerda = request.form['perna_esquerda']
        problemas_saude = request.form['problemas_saude']
        desejos = request.form['desejos']
        data = request.form['data']
        panturrilha_esquerda = request.form['panturrilha_esquerda']
        panturrilha_direita = request.form['panturrilha_direita']


        query = '''
            INSERT INTO alunos (
                usuario_id, nome, idade, altura, peso, imc,
                porcentagem_gordura, porcentagem_musculo, taxa_metabolica_basal,
                idade_media, gordura_visceral, pescoco, ombro, torax, cintura, abdominal,
                quadril, braco_direito, braco_esquerdo, braco_circulo_direito,
                braco_circulo_esquerdo, antebraco_direito, antebraco_esquerdo,
                perna_direita, perna_esquerda, problemas_saude, desejos, data,
                panturrilha_esquerda, panturrilha_direita
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s
            )
        '''
        cursor.execute(query, (
            usuario_id, nome, idade, altura, peso, imc,
            porcentagem_gordura, porcentagem_musculo, taxa_metabolica_basal,
            idade_media, gordura_visceral, pescoco, ombro, torax, cintura, abdominal,
            quadril, braco_direito, braco_esquerdo, braco_circulo_direito,
            braco_circulo_esquerdo, antebraco_direito, antebraco_esquerdo,
            perna_direita, perna_esquerda, problemas_saude, desejos, data,
            panturrilha_esquerda, panturrilha_direita
        ))

        cnx.commit()


        cursor.close()
        cnx.close()


        return redirect(url_for('aluno_routes.mostrar_aluno', nome=nome))


    return render_template('cadastro_aluno.html', usuario_id=usuario_id, nome=nome)

@aluno_routes.route('/mostrar_aluno', methods=['GET'])
def mostrar_aluno():
    nome = request.args.get('nome') 
    if not nome:
        flash('Nome do aluno não informado.', 'error')
        return redirect(url_for('menu_routes.menu'))

    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    
    query_usuario = "SELECT id FROM usuarios WHERE nome = %s"
    cursor.execute(query_usuario, (nome,))
    usuario = cursor.fetchone()

    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('menu_routes.menu'))

    usuario_id = usuario['id']

    query_aluno = "SELECT * FROM alunos WHERE usuario_id = %s"
    cursor.execute(query_aluno, (usuario_id,))
    avaliacoes = cursor.fetchall()

    cursor.close()
    cnx.close()

    if not avaliacoes:
        flash("Nenhuma avaliação encontrada para este aluno.", "info")
        return render_template('mostrar_aluno.html', nome=nome, usuario_id=usuario_id, avaliacoes=[], exibir_formulario=False)

    return render_template('mostrar_aluno.html', nome=nome, usuario_id=usuario_id, avaliacoes=avaliacoes, exibir_formulario=True)

@aluno_routes.route('/adicionar_treino/<int:user_id>', methods=['POST'])
def adicionar_treino(user_id):
    nome_treino = request.form['nome_treino']
    exercicio = request.form['exercicio']
    repeticoes = request.form['repeticoes']
    peso = request.form['peso']

    cnx = get_db_connection()
    cursor = cnx.cursor()

    query = """
    INSERT INTO treinos (usuario_id, nome_treino, exercicio, repeticoes, peso)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, nome_treino, exercicio, repeticoes, peso))
    cnx.commit()

    cursor.close()
    cnx.close()

    flash('Exercício adicionado com sucesso!', 'success')
    return redirect(url_for('aluno_routes.treinos', user_id=user_id))

@aluno_routes.route('/treinos/<int:user_id>', methods=['GET', 'POST'])
def treinos(user_id):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    treinos = []

    query_usuario = "SELECT * FROM usuarios WHERE id = %s"
    cursor.execute(query_usuario, (user_id,))
    usuario = cursor.fetchone()

    if not usuario:
        return "Usuário não encontrado", 404

    query_treinos = "SELECT * FROM treinos WHERE usuario_id = %s"   
    cursor.execute(query_treinos, (user_id,))
    treinos = cursor.fetchall()

    cursor.close()
    cnx.close()
    print(user_id)
    return render_template('treinos.html', treinos=treinos, usuario=usuario)

@aluno_routes.route('/excluir_treino/<int:user_id>', methods=['GET'])
def excluir_treino(user_id):
    nome_treino = request.args.get('nome_treino')
    exercicio = request.args.get('exercicio')

    cnx = get_db_connection()
    cursor = cnx.cursor()

    query = """
    DELETE FROM treinos 
    WHERE usuario_id = %s AND nome_treino = %s AND exercicio = %s
    """
    cursor.execute(query, (user_id, nome_treino, exercicio))
    cnx.commit()

    cursor.close()
    cnx.close()

    flash('Exercício excluído com sucesso!', 'success')
    return redirect(url_for('aluno_routes.treinos', user_id=user_id))

@aluno_routes.route('/gerenciar_treinos/<int:user_id>', methods=['GET'])
def gerenciar_treinos(user_id):
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)

    query = "SELECT nome_treino, exercicio, repeticoes, peso FROM treinos WHERE usuario_id = %s"
    cursor.execute(query, (user_id,))
    treinos = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template('gerenciar_treinos.html', treinos=treinos, usuario_id=user_id)

@aluno_routes.route('/excluir_avaliacao/<int:avaliacao_id>', methods=['POST'])
def excluir_avaliacao(avaliacao_id):
    cnx = get_db_connection()
    cursor = cnx.cursor()
    
    query = "DELETE FROM alunos WHERE id = %s"
    
    cursor.execute(query, (avaliacao_id,))
    
    cnx.commit()
    
    cursor.close()
    cnx.close()

    flash('Avaliação excluída com sucesso!', 'success')
    return redirect(url_for('aluno_routes.mostrar_aluno', nome=request.args.get('nome')))
