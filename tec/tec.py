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
            conexao = conecta_database()  # Agora chama a função aqui, no momento apropriado
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

            return render_template("tecHome.html", chamados=chamados, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")
    
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

            # Adicione o filtro pela ID do chamado diretamente na consulta
            query = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, ca.nomeCargo, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                JOIN cargo ca ON u.idCargo = ca.idCargo
                WHERE c.idChamado = %s
            """
            cursor.execute(query, (idChamado,))
            chamado = cursor.fetchone()  # Pega apenas um chamado

            # Verifica se o chamado foi encontrado
            if chamado:
                return render_template("tecMore.html", chamado=chamado, title="Administração", login=True)
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


@tec_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_FOLDER, filename)
