from flask import render_template, Blueprint, redirect, send_from_directory, request, jsonify
from session.session import verifica_sessao
from connection.connection import conecta_database  # Importando corretamente
import os

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
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, ca.nomeCargo, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
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
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor()

            # Atualiza o status do chamado para concluído (supondo que o ID do status "concluído" seja 3)
            update_query = """
                UPDATE chamado
                SET idStatus = 3
                WHERE idChamado = %s
            """
            cursor.execute(update_query, (idChamado,))
            conexao.commit()  # Confirma as mudanças no banco de dados

            return jsonify({"message": "Chamado finalizado com sucesso."}), 200
        except Exception as e:
            print(f"Erro ao finalizar o chamado: {e}")
            return jsonify({"message": "Erro ao finalizar o chamado."}), 500
        finally:
            conexao.close()
    else:
        return jsonify({"message": "Usuário não autorizado."}), 403


@tec_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_FOLDER, filename)
