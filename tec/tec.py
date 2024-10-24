from flask import render_template, Blueprint, redirect, send_from_directory, request, jsonify
from session.session import verifica_sessao
from connection.connection import conecta_database  # Importando corretamente
import os
from datetime import datetime

tec_blueprint = Blueprint("tec", __name__, template_folder="templates")

IMG_FOLDER = os.path.join('src', 'img')

# Rota para a página inicial da manutenção
@tec_blueprint.route('/tecHome')
def tec_home():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            query = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, ca.nomeCargo, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                JOIN cargo ca ON u.idCargo = ca.idCargo
                WHERE c.idStatus != 3
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title = "Manutenção"

            # Armazena a quantidade inicial de chamados
            quantidade_inicial = len(chamados)

            return render_template("tecHome.html", chamados=chamados, title=title, login=True, quantidade_inicial=quantidade_inicial)
        finally:
            conexao.close()
    else:
        return redirect("/login")

@tec_blueprint.route('/tecHome/novosChamados')
def novos_chamados():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Consulta para contar chamados ativos
            query = """
                SELECT COUNT(*) AS total
                FROM chamado
                WHERE idStatus != 3
            """
            cursor.execute(query)
            resultado = cursor.fetchone()
            total_chamados = resultado['total']

            # Compare com a quantidade inicial (armazenada na sessão ou passada como parâmetro)
            quantidade_inicial = request.args.get('quantidade_inicial', 0, type=int)

            return jsonify(novosChamados=total_chamados > quantidade_inicial)
        finally:
            conexao.close()
    else:
        return jsonify(novosChamados=False)


@tec_blueprint.route('/tecTask')
def tec_task():
    if verifica_sessao():
        try:
            conexao = conecta_database()  # Agora chama a função aqui, no momento apropriado
            cursor = conexao.cursor(dictionary=True)

            query = """
                SELECT c.descChamado, c.concChamado, u.nomeUsuario, ca.nomeCargo, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                JOIN cargo ca ON u.idCargo = ca.idCargo
                WHERE c.idStatus = 3
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title = "Finalizados"
            return render_template("tecTask.html", chamados=chamados, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")

    

@tec_blueprint.route('/tecMore/<int:idChamado>')
def tec_more(idChamado):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Consulta para pegar os detalhes do chamado
            query_chamado = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, ca.nomeCargo, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                JOIN cargo ca ON u.idCargo = ca.idCargo
                WHERE c.idChamado = %s
            """
            cursor.execute(query_chamado, (idChamado,))
            chamado = cursor.fetchone()

            # Consulta para pegar as respostas associadas ao chamado
            query_respostas = """
                SELECT r.descResposta, r.dataResposta
                FROM resposta r
                WHERE r.idChamado = %s
            """
            cursor.execute(query_respostas, (idChamado,))
            respostas = cursor.fetchall()

            if chamado:
                return render_template("tecMore.html", chamado=chamado, respostas=respostas, title="Administração", login=True)
            else:
                return "Chamado não encontrado", 404
        finally:
            conexao.close()
    else:
        return redirect("/login")



@tec_blueprint.route('/tec/finalizarChamado/<int:idChamado>', methods=['POST'])
def finalizar_chamado(idChamado):
    try:
        # Conecta ao banco de dados e busca o chamado pelo ID
        print("Conectando ao banco de dados...")
        conn = conecta_database()
        cursor = conn.cursor()

        # Define a data atual
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Data atual: {data_atual}")

        # Atualiza o idStatus e a data de finalização do chamado
        cursor.execute("""
            UPDATE chamado
            SET idStatus = 3, concChamado = %s
            WHERE idChamado = %s
        """, (data_atual, idChamado))
        
        print("Chamado atualizado, aplicando mudanças...")
        # Confirma a transação e fecha a conexão
        conn.commit()

        cursor.close()
        conn.close()
        print("Chamado finalizado com sucesso!")

        return jsonify({'message': 'Chamado finalizado com sucesso!'}), 200

    except Exception as e:
        print(f"Erro ao finalizar chamado: {e}")
        return jsonify({'error': str(e)}), 500


@tec_blueprint.route('/tec/addResponse/<int:idChamado>', methods=['POST'])
def add_response(idChamado):
    try:
        # Conecta ao banco de dados
        conn = conecta_database()
        cursor = conn.cursor()

        # Obtém a resposta enviada pelo frontend
        data = request.get_json()
        resposta = data.get('resposta')

        # Define a data atual
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insere a resposta no banco de dados
        cursor.execute("""
            INSERT INTO resposta (descResposta, dataResposta, idChamado)
            VALUES (%s, %s, %s)
        """, (resposta, data_atual, idChamado))

        # Atualiza o idStatus do chamado para "respondido"
        cursor.execute("""
            UPDATE chamado
            SET idStatus = 2  -- Supondo que 2 seja o ID para o status "respondido"
            WHERE idChamado = %s
        """, (idChamado,))

        # Confirma a transação e fecha a conexão
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"Erro ao adicionar resposta: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500



@tec_blueprint.route('/tec/chamado/<int:id>')
def detalhe(id):
    conn = conecta_database()  # Conecte ao banco de dados
    cursor = conn.cursor(dictionary=True)

    # Consulta para obter os detalhes do chamado
    cursor.execute("SELECT * FROM Chamado WHERE idChamado = %s", (id,))
    chamado = cursor.fetchone()

    # Consulta para obter as respostas do chamado
    cursor.execute("SELECT * FROM Resposta WHERE idChamado = %s", (id,))
    respostas = cursor.fetchall()

    cursor.close()
    conn.close()

    if not chamado:
        return "Chamado não encontrado", 404

    return render_template('chamado.html', chamado=chamado, respostas=respostas)



@tec_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_FOLDER, filename)
