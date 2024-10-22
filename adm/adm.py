from flask import render_template, redirect, Blueprint, request, flash, url_for, session
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import uuid

# Definindo o blueprint para administração
adm_blueprint = Blueprint("adm", __name__, template_folder="templates")

@adm_blueprint.route("/adm")
def adm():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Obter o idUsuario da sessão
            id_usuario = session.get('idUsuario')
            if id_usuario is None:
                flash('Você precisa estar logado para visualizar seus chamados!', 'error')
                return redirect('/login')

            # Consulta para obter os últimos 3 chamados do usuário logado
            query_ultimos_chamados = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE c.idUsuario = %s
                ORDER BY c.dataChamado DESC
                LIMIT 3
            """
            cursor.execute(query_ultimos_chamados, (id_usuario,))
            ultimos_chamados = cursor.fetchall()

            # Consulta para obter a contagem total de chamados por status
            query_totais = """
                SELECT 
                SUM(CASE WHEN s.nomeStatus = 'Não Respondido' THEN 1 ELSE 0 END) AS nao_respondidos,
                SUM(CASE WHEN s.nomeStatus = 'Respondido' THEN 1 ELSE 0 END) AS respondidos,
                SUM(CASE WHEN s.nomeStatus = 'Concluído' THEN 1 ELSE 0 END) AS concluidos
                FROM chamado c
                JOIN status s ON c.idStatus = s.idStatus
            """

            cursor.execute(query_totais)
            totais_chamados = cursor.fetchone()  # Obtemos um dicionário com as contagens


            return render_template("adm.html", ultimos_chamados=ultimos_chamados, totais_chamados=totais_chamados, title="Administração", login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")



# Rota para cadastro de chamado
@adm_blueprint.route("/cadchamados", methods=['GET', 'POST'])
def cadchamados():
    login = verifica_sessao()

    try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            if request.method == 'POST':
                # Obter o idUsuario da sessão
                id_usuario = session.get('idUsuario')  # Usando get() para evitar KeyError
                print(id_usuario)
                if id_usuario is None:
                    flash('Você precisa estar logado para cadastrar um chamado!', 'error')
                    return redirect('/login')

                # Obter os dados do formulário
                area = request.form.get('area')
                local = request.form.get('local')
                item = request.form.get('item')
                descricao = request.form.get('descricao')
                
                imagem = request.files.get('imagem')  # Para imagem enviada

                # Verifica se a imagem foi enviada
                if not imagem:
                    flash('A imagem é obrigatória para cadastrar um chamado!', 'error')
                    return redirect('/cadchamados')

                # Gerar um nome único para a imagem
                id_foto = str(uuid.uuid4().hex)
                filename = f"{id_foto}_{item}.png"
                imagem.save(os.path.join("static/img/chamados", filename))  # Corrigido para o diretório correto

                cursor.execute(""" 
                    INSERT INTO chamado (descChamado, imgChamado, idItem, idLocal, idUsuario, idStatus, dataChamado) 
                    VALUES (%s, %s, %s, %s, %s, 1, NOW())  -- Assumindo que o status inicial é '1'
                """, (descricao, filename, item, local, id_usuario))

                conexao.commit()
                flash('Chamado cadastrado com sucesso!', 'success')
                return redirect(url_for('adm.adm'))

            # Obtenção dos dados para o formulário
            cursor.execute('SELECT * FROM local')
            locais = cursor.fetchall()

            cursor.execute('SELECT * FROM item')
            itens = cursor.fetchall()

            cursor.execute("SELECT idArea, nomeArea FROM area")
            areas = cursor.fetchall()

            cursor.execute("SELECT idUsuario, nomeUsuario FROM usuario")
            usuarios = cursor.fetchall()

            cursor.execute("SELECT idCargo, nomeCargo FROM cargo")
            cargos = cursor.fetchall()

            title = "Cadastro de chamado"
            return render_template("cadchamados.html", title=title, login=login, locais=locais, itens=itens, areas=areas, usuarios=usuarios, cargos=cargos)
    finally:
        conexao.close()


# Rota para cadUsuario
@adm_blueprint.route("/cadUsuario", methods=['GET', 'POST'])
def cadastroUsuario():
    if request.method == 'POST':
        # Obter os dados do formulário
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('nome_email')
        cargo = request.form.get('cargo')
        data_nascimento = request.form.get('data_nascimento')
        numero = request.form.get('numero')

        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Inserindo o novo usuário no banco de dados
            cursor.execute("""
                INSERT INTO usuario (nomeUsuario, emailUsuario, idCargo, dataNascimento, numero)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome_completo, email, cargo, data_nascimento, numero))

            conexao.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('adm.cadastroUsuario')) 

        except Exception as e:
            flash('Erro ao cadastrar usuário: ' + str(e), 'error')
            return redirect(url_for('adm.cadastroUsuario'))  # Redireciona em caso de erro

        finally:
            conexao.close()
    else:
        # Método GET: buscar cargos
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute("SELECT idCargo, nomeCargo FROM cargo")
            cargos = cursor.fetchall()

            title = "Cadastro de Usuário"
            return render_template("cadUsuario.html", title=title, login=True, cargos=cargos)

        finally:
            conexao.close()


# Rota para exibir mais informações sobre um chamado
@adm_blueprint.route("/vermais/<int:idChamado>")
def sobre(idChamado):
    if verifica_sessao():
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chamado WHERE idChamado = %s", (idChamado,))
        chamado = cursor.fetchone()
        conexao.close()
        title = "Ver Mais"
        return render_template("vermais.html", title=title, chamado=chamado)
    else:
        return redirect("/login")

# Rota para cadItem
@adm_blueprint.route("/cadItem")
def cadastroItem():
    title = "CADASTRO ITEM"
    return render_template("cadItem.html", title=title, login=True)

# Rota para cadLocal
@adm_blueprint.route("/cadLocal", methods=['GET', 'POST'])
def cadLocal():
    if request.method == 'POST':
        nome_local = request.form.get('nome_local')
        descricao = request.form.get('descricao')

        try:
            conexao = conecta_database()
            cursor = conexao.cursor()

            # Comando de inserção
            cursor.execute("""
                INSERT INTO local (nomeLocal, descricao) 
                VALUES (%s, %s)
            """, (nome_local, descricao))

            conexao.commit()
            flash('Local cadastrado com sucesso!', 'success')
            return redirect(url_for('adm.adm'))  # Redireciona após o cadastro

        except Exception as e:
            flash(f'Erro ao cadastrar local: {str(e)}', 'error')
            return redirect(url_for('adm.cadLocal'))  # Corrigido para usar o nome certo da rota

        finally:
            conexao.close()

    return render_template("cadLocal.html", title="Cadastro de Local", login=True)



# Rota para filtrarItemedicao
@adm_blueprint.route("/filtrarItemedicao")
def filtrarItemedicao():
    title = "Filtrar Item Edição"
    return render_template("filtrarItemedicao.html", title=title, login=True)

# Rota para filtrarLocaledicao
@adm_blueprint.route("/filtrarLocaledicao")
def filtrarLocaledicao():
    title = "Filtrar Local Edição"
    return render_template("filtrarLocaledicao.html", title=title, login=True)

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
        cursor.execute('SELECT imgChamado FROM chamado WHERE idChamado = %s', (idChamado,))
        chamado = cursor.fetchone()

        # Excluindo a imagem do chamado do diretório de imagens
        if chamado and chamado['imgChamado']:
            try:
                os.remove(os.path.join("static/img/chamados", chamado['imgChamado']))
            except FileNotFoundError:
                pass  # Se o arquivo não for encontrado, continuamos sem falhar

        # Excluindo o chamado do banco de dados
        cursor.execute('DELETE FROM chamado WHERE idChamado = %s', (idChamado,))
        conexao.commit()
        conexao.close()

        return redirect('/adm')
    else:
        return redirect("/login")
