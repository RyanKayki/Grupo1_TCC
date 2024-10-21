from flask import render_template, Blueprint, redirect, send_from_directory
from session.session import verifica_sessao
from connection.connection import conecta_database  # Importando corretamente
import os

func_blueprint = Blueprint("func", __name__, template_folder="templates")

# Rota para a página inicial dos funcionários
@func_blueprint.route('/funcHome')
def func_home():
    if verifica_sessao():
        try:
            conexao = conecta_database()  # Agora chama a função aqui, no momento apropriado
            cursor = conexao.cursor(dictionary=True)

            query = """
                SELECT c.descChamado, c.dataChamado, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idItem, c.idLocal, r.descResposta
                FROM chamado c
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                JOIN resposta r ON c.idChamado = r.idChamado
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title="Manutenção"


            return render_template("funcHome.html", chamados=chamados, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")

# Rota para ver detalhes do chamado
@func_blueprint.route('/detalhe_chamado/<int:idChamado>')
def detalhe_chamado(idChamado):
        if verifica_sessao():
            try:
                conexao = conecta_database()  # Agora chama a função aqui, no momento apropriado
                cursor = conexao.cursor(dictionary=True)
                query = """
                    SELECT c.descChamado, c.concChamado, c.imgChamado, l.nomeLocal, i.nomeItem, s.nomeStatus, r.descResposta, r.dataResposta
                    FROM chamado c
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    JOIN resposta r ON c.idChamado = r.idChamado
                    WHERE c.idChamado = %s
                """
                cursor = conexao.execute(query, (idChamado,))
                infos = cursor.fetchone()
                title = "Detalhes do Chamado"
                return render_template('details.html', title=title, infos=infos, login=True)
            finally:
                 conexao.close()
        else:
            return redirect("/login")
        

# Rota para cadastro de funcionário (lógica a ser implementada)
@func_blueprint.route("/cadastro_funcionario", methods=['POST'])
def cadastro_funcionario_json():
    # Implementar lógica de cadastro de funcionário aqui
    pass

# Rota do perfil do funcionário
@func_blueprint.route("/Perfil_funcionario", methods=['POST'])
def perfil_func():
    # Implementar lógica da tela de perfil
    pass
