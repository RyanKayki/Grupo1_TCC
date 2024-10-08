from flask import render_template, Blueprint, redirect, send_from_directory
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
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, u.cargoUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idItem, c.idLocal
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE c.idStatus != 3
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title="Manutenção"


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
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, u.cargoUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idItem, c.idLocal
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE c.idStatus = 3
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title="Finalizados"
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
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, u.cargoUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idItem, c.idLocal
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
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


@tec_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMG_FOLDER, filename)
    
