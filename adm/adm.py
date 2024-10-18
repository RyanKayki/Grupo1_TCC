from flask import render_template, redirect, Blueprint, request, flash, url_for
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import mysql.connector, uuid, os

conexaoDB = conecta_database()

# Definindo o blueprint para administração
adm_blueprint = Blueprint("adm", __name__, template_folder="templates")

@adm_blueprint.route("/adm")
def adm():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            query = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                """
            cursor.execute(query)
            chamados = cursor.fetchall()

            return render_template("adm.html", chamados=chamados, title="Administração", login=True)  # redirecionar para uma página de erro
        finally:
            conexao.close()
    else:
        return redirect("/login")


# Rota para cadastro de chamado
@adm_blueprint.route("/cadchamados", methods=['GET', 'POST'])
def cadchamados():
    login = verifica_sessao()
    if login:
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            if request.method == 'POST':
                # Obter os dados do formulário
                area = request.form.get('area')
                local = request.form.get('local')
                item = request.form.get('item')
                descricao = request.form.get('descricao')
                imagem = request.files.get('imagem')  # Para imagem enviada
                
                # Lógica para salvar os dados no banco de dados
                cursor.execute("""
                    INSERT INTO Chamado (descChamado, imgChamado, idItem, idLocal, idUsuario, idStatus, dataChamado) 
                    VALUES (%s, %s, %s, %s, %s, 1, NOW())  -- Assumindo que o status inicial é '1'
                """, (descricao, imagem.filename if imagem else None, item, local, login['idUsuario']))

                conexao.commit()
                flash('Chamado cadastrado com sucesso!', 'success')
                return redirect('/cadchamados')

            # Obtenção dos dados para o formulário
            cursor.execute('SELECT * FROM local')
            locais = cursor.fetchall()

            cursor.execute('SELECT * FROM item')
            itens = cursor.fetchall()

            cursor.execute("SELECT idArea, nomeArea FROM Area")
            areas = cursor.fetchall()

            title = "Cadastro de chamado"
            return render_template("cadchamados.html", title=title, login=login, locais=locais, itens=itens, areas=areas)
        finally:
            conexao.close()
    else:
        return redirect("/login")




# Rota para exibir mais informações sobre um chamado
@adm_blueprint.route("/vermais/<int:idChamado>")
def sobre(idChamado):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chamado WHERE idChamado = %s", (idChamado,))
    chamado = cursor.fetchall()
    conexao.close()
    title = "Ver Mais"
    return render_template("vermais.html", title=title, chamado=chamado)


# Rota para cadItem
@adm_blueprint.route("/cadItem")
def cadastroItem():
    title = "CADASTRO ITEM"
    return render_template("cadItem.html", title=title, login=True)

# Rota para cadUsuario
@adm_blueprint.route("/cadUsuario")
def cadastroUsuario():
    title = "CADASTRO USUÁRIO"
    return render_template("cadUsuario.html", title=title, login=True)

# Rota para cadLocal
@adm_blueprint.route("/cadLocal")
def cadastroLocal():
    title = "CADASTRO LOCAL"
    return render_template("cadLocal.html", title=title, login=True)


# Rota para filtrarItem
@adm_blueprint.route("/filtrarItem")
def filtrarItem():
    title = "Filtrar Item"
    return render_template("filtrarItem.html", title=title, login=True)

# Rota para filtrarLocal
@adm_blueprint.route("/filtrarLocal")
def filtrarLocal():
    title = "Filtrar Local"
    return render_template("filtrarLocal.html", title=title, login=True)


# Rota para edicaoLocal
@adm_blueprint.route("/edicaoLocal")
def edicaoLocal():
    title = "Edição de Local"
    return render_template("edicaoLocal.html", title=title, login=True)

# Rota para edicaoItem
@adm_blueprint.route("/edicaoItem")
def edicaoItem():
    title = "Edição de Item"
    return render_template("edicaoItem.html", title=title, login=True)


@adm_blueprint.route("/excluir/<int:idChamado>")
def excluir(idChamado):
    # Rota para excluir um chamado
    if verifica_sessao():
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscando a imagem associada ao chamado
        cursor.execute('SELECT img_chamado FROM chamado WHERE idChamado = %s', (idChamado,))
        chamado = cursor.fetchone()
        
        # Excluindo a imagem do chamado do diretório de imagens
        if chamado and chamado['img_chamado']:
            try:
                os.remove(os.path.join("static/img/chamado/", chamado['img_chamado']))
            except FileNotFoundError:
                pass  # Se o arquivo não for encontrado, continuamos sem falhar

        # Excluindo o chamado do banco de dados
        cursor.execute('DELETE FROM chamado WHERE idChamado = %s', (idChamado,))
        conexao.commit()
        conexao.close()
        
        return redirect('/adm')
    else:
        return redirect("/login")
