from flask import render_template, redirect, Blueprint, request, flash, url_for, session, jsonify, send_from_directory
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import uuid
from datetime import datetime
import ast # Biblioteca para converter string em dicionário
from collections import defaultdict # permite renderizar o ano apenas uma vez quando o ano muda.

# Definindo o blueprint para administração
adm_blueprint = Blueprint("adm", __name__, template_folder="templates")

IMG_FOLDER = os.path.join('src', 'img')

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
                if imagem:
                    # Gerar um nome único para a imagem
                    id_foto = str(uuid.uuid4().hex)
                    filename = f"{id_foto}_{item}.png"
                    imagem.save(os.path.join("src/img/chamados", filename))

                    cursor.execute(""" 
                        INSERT INTO chamado (descChamado, imgChamado, idItem, idLocal, idUsuario, idStatus, dataChamado) 
                        VALUES (%s, %s, %s, %s, %s, 1, NOW())
                    """, (descricao, filename, item, local, id_usuario))
                else:
                    cursor.execute(""" 
                        INSERT INTO chamado (descChamado, idItem, idLocal, idUsuario, idStatus, dataChamado) 
                        VALUES (%s, %s, %s, %s, 1, NOW())
                    """, (descricao, item, local, id_usuario))  # Corrigi aqui removendo o parâmetro extra

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


@adm_blueprint.route("/filtrarLocais/<int:idArea>", methods=['GET'])
def filtrarLocais(idArea):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    
    # Filtrar locais relacionados à área
    query = """
    SELECT idLocal, nomeLocal FROM local WHERE idArea = %s
    """
    cursor.execute(query, (idArea,))
    locais = cursor.fetchall()
    
    conexao.close()
    
    # Retorna os locais como JSON
    return jsonify(locais)


@adm_blueprint.route("/filtrarItens/<int:idLocal>", methods=['GET'])
def filtrarItens(idLocal):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    # Primeiro, obtém a categoria do local selecionado
    query_categoria = "SELECT idCategoria FROM local WHERE idLocal = %s"
    cursor.execute(query_categoria, (idLocal,))
    categoria = cursor.fetchone()

    if categoria:
        idCategoria = categoria['idCategoria']

        # Filtrar itens relacionados à categoria do local
        query_itens = """
        SELECT i.idItem, i.nomeItem
        FROM item i
        JOIN item_categoria ic ON i.idItem = ic.idItem
        WHERE ic.idCategoria = %s
        """
        cursor.execute(query_itens, (idCategoria,))
        itens = cursor.fetchall()
    else:
        itens = []

    conexao.close()

    # Retorna os itens como JSON
    return jsonify(itens)


# Rota para a página de lista de locais
@adm_blueprint.route("/chamadosalas/<int:idArea>", methods=['GET'])
def chamadoSalas(idArea):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    query = """
    SELECT c.nomeCategoria, GROUP_CONCAT(l.nomeLocal SEPARATOR ', ') AS locais
    FROM categoria c
    JOIN local l ON c.idCategoria = l.idCategoria
    GROUP BY c.nomeCategoria
    WHERE l.idArea = %s;
    """

    cursor.execute(query, (idArea,))
    locais = cursor.fetchall()

    query = """
    SELECT nomeArea FROM area WHERE idArea = %s
    """

    cursor.execute(query, (idArea,))
    area = cursor.fetchone()
    conexao.close()

    return render_template("chamadoSalas.html", title="Lista de salas", locais=locais, area=area)

# Rota para cadUsuario
@adm_blueprint.route("/cadUsuario", methods=['GET', 'POST'])
def cadastroUsuario():
    if request.method == 'POST':
        # Obter os dados do formulário
        nome_completo = request.form.get('nome_completo')
        senha = request.form.get('senha')
        email = request.form.get('email')
        imagem = request.files.get('imagem')
        cargo = request.form.get('cargo') # Retorna um dicionário, mas no formato string
        cargo = ast.literal_eval(cargo) # Converte a string para dicionário
        cargo = cargo["idCargo"] # Filtra apenas o valor 
        numero = request.form.get('numero')

        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)
             # Verifica se a imagem foi enviada
            if imagem:
                # Gerar um nome único para a imagem
                id_foto = str(uuid.uuid4().hex)
                filename = f"{id_foto}_{nome_completo}.png"
                imagem.save(os.path.join("src/img/usuarios", filename))

                cursor.execute(""" 
                    INSERT INTO usuario (nomeUsuario, emailUsuario, senhaUsuario, numeroUsuario, imgUsuario, idCargo, ) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (nome_completo, email, senha, numero, filename, cargo))
            else:
                cursor.execute(""" 
                    INSERT INTO usuario (nomeUsuario, emailUsuario, senhaUsuario, numeroUsuario, idCargo) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (nome_completo, email, senha, numero, cargo))  # Corrigi aqui removendo o parâmetro extra
            

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
@adm_blueprint.route("/cadItem", methods=['GET', 'POST'])
def cadastroItem():
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute('SELECT * FROM categoria')
    categorias = cursor.fetchall()
    try:
        if request.method == 'POST':
            nome_item = request.form.get("nome_item")
            categorias_selecionadas = request.form.getlist('categorias')

            # Primeiro, insere o item na tabela 'item'
            cursor.execute("INSERT INTO item (nomeItem) VALUES (%s)", (nome_item,))
            conexao.commit()

            # Pega o ID do item recém-inserido
            idItem = cursor.lastrowid

            # Insere cada categoria selecionada na tabela de associação 'item_categoria'
            for idCategoria in categorias_selecionadas:
                cursor.execute(
                    "INSERT INTO item_categoria (idItem, idCategoria) VALUES (%s, %s)",
                    (idItem, idCategoria)
                )
            conexao.commit()
            flash('Item cadastrado com sucesso!', 'success')
            return redirect(url_for('adm.adm'))

    except Exception as e:
            flash(f'Erro ao cadastrar item: {str(e)}', 'error')
            return redirect(url_for('adm.adm'))  # Corrigido para usar o nome certo da rota

    finally:
        conexao.close()
    return render_template("cadItem.html", title="Cadastrar Item", categorias=categorias, login=True)

#Rota para edição dos itens
@adm_blueprint.route("/updateItem", methods=['GET', 'POST'])
def updateItem():
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    # Busca todas as categorias disponíveis
    cursor.execute('SELECT * FROM categoria')
    categorias = cursor.fetchall()

    # Identifica o ID do item para edição
    item_id = request.args.get("id")
    if not item_id:
        flash('Item não encontrado para edição.', 'error')
        return redirect(url_for('adm.adm'))

    # Busca os dados do item e suas categorias associadas
    cursor.execute('SELECT * FROM item WHERE idItem = %s', (item_id,))
    item = cursor.fetchone()

    cursor.execute('SELECT idCategoria FROM item_categoria WHERE idItem = %s', (item_id,))
    categorias_item = [cat['idCategoria'] for cat in cursor.fetchall()]

    print("Categorias associadas ao item:", categorias_item)  # Verifique se a lista está correta

    try:
        if request.method == 'POST':
            nome_item = request.form.get("nome_item")
            categorias_selecionadas = request.form.getlist('categorias')

            # Atualiza o item na tabela 'item'
            cursor.execute("UPDATE item SET nomeItem = %s WHERE idItem = %s", (nome_item, item_id))
            
            # Atualiza as categorias associadas, removendo as antigas e inserindo as novas
            cursor.execute("DELETE FROM item_categoria WHERE idItem = %s", (item_id,))
            for idCategoria in categorias_selecionadas:
                cursor.execute(
                    "INSERT INTO item_categoria (idItem, idCategoria) VALUES (%s, %s)",
                    (item_id, idCategoria)
                )
            conexao.commit()
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('adm.adm'))

    except Exception as e:
        flash(f'Erro ao atualizar item: {str(e)}', 'error')
        return redirect(url_for('adm.adm'))

    finally:
        conexao.close()

    return render_template("updateItem.html", title="Editar Item", item=item, categorias=categorias, categorias_item=categorias_item, login=True)



# Rota para cadLocal
@adm_blueprint.route("/cadLocal", methods=['GET', 'POST'])
def cadLocal():
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute('SELECT * FROM categoria')
    categorias = cursor.fetchall()

    cursor.execute("SELECT * FROM area")
    areas = cursor.fetchall()

    if request.method == 'POST':
        nome_local = request.form.get('nome_local')
        area = request.form.get('area')
        categoria = request.form.get('categoria')

        try:

            # Comando de inserção
            cursor.execute("""
                INSERT INTO local (nomeLocal, idCategoria, idArea) 
                VALUES (%s, %s, %s)
            """, (nome_local, categoria, area,))

            conexao.commit()
            flash('Local cadastrado com sucesso!', 'success')
            return redirect(url_for('adm.adm'))  # Redireciona após o cadastro

        except Exception as e:
            flash(f'Erro ao cadastrar local: {str(e)}', 'error')
            return redirect(url_for('adm.cadLocal'))  # Corrigido para usar o nome certo da rota

        finally:
            conexao.close()

    return render_template("cadLocal.html", title="Cadastro de Local", categorias=categorias, areas=areas, login=True)



# Rota para perfil
@adm_blueprint.route("/perfil")
def perfil():
    if verifica_sessao():
        # Obter o idUsuario da sessão
        id_usuario = session.get('idUsuario')
        if id_usuario is None:
            flash('Você precisa estar logado para acessar o perfil.', 'error')
            return redirect('/login')

        # Conectar ao banco e buscar dados do usuário logado
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)

        try:
            query_usuario = """
                SELECT u.nomeUsuario, u.emailUsuario, u.numeroUsuario, u.imgUsuario, c.nomeCargo
                FROM usuario u
                JOIN cargo c ON u.idCargo = c.idCargo
                WHERE u.idUsuario = %s
            """
            cursor.execute(query_usuario, (id_usuario,))
            usuario = cursor.fetchone()  # Obtemos um dicionário com os dados do usuário

            # Renderizar o template com os dados do usuário
            title = "Perfil"
            return render_template("perfil.html", title=title, login=True, usuario=usuario)

        finally:
            conexao.close()
    else:
        return redirect("/login")


# Rota para filtrarItemedicao
@adm_blueprint.route("/filtrarItemedicao")
def filtrarItemedicao():
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Consulta para obter todas as salas
        query_salas = "SELECT idLocal, nomeLocal FROM local"
        cursor.execute(query_salas)
        salas = cursor.fetchall()

    finally:
        # Fecha a conexão com o banco de dados
        conexao.close()

    # Renderiza o template e passa a lista de salas
    title = "Filtrar Item Edição"
    return render_template("filtrarItemedicao.html", title=title, salas=salas)


# Rota para filtrarLocaledicao
@adm_blueprint.route("/filtrarLocaledicao")
def filtrarLocaledicao():
    # Conectar ao banco de dados
    conn = conecta_database()
    cursor = conn.cursor()

    # Consultar dados das areas
    cursor.execute("SELECT idArea, nomeArea FROM `area`")
    locais = cursor.fetchall()

     # Consultar dados das categorias
    cursor.execute("SELECT idCategoria, nomeCategoria FROM `categoria`")
    categorias = cursor.fetchall()

    # Fechar conexão
    cursor.close()
    conn.close()

    # Renderizar template passando os locais
    title = "Filtrar Local Edição"
    return render_template("filtrarLocaledicao.html", title=title, login=True, salas=locais, categorias=categorias)

# Rota para edicaoLocal
@adm_blueprint.route("/edicaoLocal")
def edicaoLocal():
    title = "Edição de Local"
    return render_template("edicaoLocal.html", title=title, login=True)

# Rota para editar um item específico
@adm_blueprint.route("/edicaoItem/<int:id_item>")
def edicaoItem(id_item):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Confirme que o campo idItem está correto no banco de dados
        query_item = "SELECT * FROM item WHERE idItem = %s"  # ou `id` se esse for o nome correto
        cursor.execute(query_item, (id_item,))
        item = cursor.fetchone()
    finally:
        conexao.close()

    title = "Edição de Item"
    return render_template("edicaoItem.html", title=title, item=item, login=True)


@adm_blueprint.route("/chamadosSala")
def ChamadosSala():
    title = "Chamados Da Sala"
    return render_template("chamadoSalas.html", title=title, login=True)

@adm_blueprint.route("/chamadoDetalhes/<int:id_chamado>")
def DetalheChamado(id_chamado):
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
            cursor.execute(query_chamado, (id_chamado,))
            chamado = cursor.fetchone()

            # Consulta para pegar as respostas associadas ao chamado
            query_respostas = """
                SELECT r.descResposta, r.dataResposta
                FROM resposta r
                WHERE r.idChamado = %s
            """
            cursor.execute(query_respostas, (id_chamado,))
            respostas = cursor.fetchall()

            if chamado:
                return render_template("chamadoDetalhes.html", chamado=chamado, respostas=respostas, title="Detalhes do Chamado", login=True)
            else:
                return "Chamado não encontrado", 404
        finally:
            conexao.close()
    else:
        return redirect("/login")



# Registro de Chamados - Histórico de chamados agrupados por data
@adm_blueprint.route("/registroChamados")
def registroChamado():
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
                ORDER BY c.dataChamado DESC
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title = "Registro de Chamados"
            titulo_pagina = "Registro de Chamados"

            # Organizando por ano e data formatada (sem o ano na chave de data)
            chamados_por_ano = defaultdict(lambda: defaultdict(list))

            # Verifica se há chamados para o usuário logado
            if not chamados:
                flash("Nenhum chamado cadastrado no momento.", "info")
                return render_template("listaChamados.html", chamados_por_ano={}, title=title, titulo_pagina=titulo_pagina, login=True)
            
            for chamado in chamados:
                data = chamado['dataChamado']
                dia_semana = dias_da_semana[data.weekday()]
                dia = data.day
                mes = meses[data.month]
                ano = data.year

                # Data formatada sem o ano
                data_formatada = f"{dia_semana}, {dia} de {mes}"

                # Agrupar chamados por ano e por data
                chamados_por_ano[ano][data_formatada].append(chamado)

            return render_template("listaChamados.html", chamados_por_ano=chamados_por_ano, titulo_pagina=titulo_pagina, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")


# Registro de Chamados - Histórico de chamados do usuario
@adm_blueprint.route("/registroChamadosUsuario")
def registroChamadosUsuario():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Obtém o ID do usuário logado
            id_usuario = session.get('idUsuario')

            query = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE c.idUsuario = %s
                ORDER BY c.dataChamado DESC
            """
            cursor.execute(query, (id_usuario,))
            chamados = cursor.fetchall()
            title = "Meus Chamados"
            titulo_pagina = "Meus Chamados"

            # Verifica se há chamados para o usuário logado
            if not chamados:
                flash("Nenhum chamado cadastrado no momento.", "info")
                return render_template("listaChamados.html", chamados_por_ano={}, title=title, titulo_pagina=titulo_pagina, login=True)

            # Agrupar chamados por ano e data
            chamados_por_ano = defaultdict(lambda: defaultdict(list))
            for chamado in chamados:
                data = chamado['dataChamado']
                dia_semana = dias_da_semana[data.weekday()]
                dia = data.day
                mes = meses[data.month]
                ano = data.year

                # Formatação da data (sem o ano)
                data_formatada = f"{dia_semana}, {dia} de {mes}"

                # Agrupar chamados por ano e por data formatada
                chamados_por_ano[ano][data_formatada].append(chamado)

            return render_template("listaChamados.html", chamados_por_ano=chamados_por_ano, titulo_pagina=titulo_pagina, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")


@adm_blueprint.route("/registroChamados/status/<status>")
def registroChamadoPorStatus(status):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Filtra a consulta pelo status
            query = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE s.nomeStatus = %s
                ORDER BY c.dataChamado DESC
            """
            cursor.execute(query, (status,))
            chamados = cursor.fetchall()
            title = "Registro de Chamados"
            titulo_pagina = f"Chamados - {status.capitalize()}"

            # Organizando por ano e data formatada (sem o ano na chave de data)
            chamados_por_ano = defaultdict(lambda: defaultdict(list))

            if not chamados:
                flash(f"Nenhum chamado com o status '{status}' encontrado.", "info")
                return render_template("listaChamados.html", chamados_por_ano={}, title=title, titulo_pagina=titulo_pagina, login=True)

            for chamado in chamados:
                data = chamado['dataChamado']
                dia_semana = dias_da_semana[data.weekday()]
                dia = data.day
                mes = meses[data.month]
                ano = data.year

                # Data formatada sem o ano
                data_formatada = f"{dia_semana}, {dia} de {mes}"

                # Agrupar chamados por ano e por data
                chamados_por_ano[ano][data_formatada].append(chamado)

            return render_template("listaChamados.html", chamados_por_ano=chamados_por_ano, titulo_pagina=titulo_pagina, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")
    
# Filtragem dos chamados por status, item, local ou chamados do usuário
@adm_blueprint.route("/filtrarchamados/<filtro>/<id>")
def filtrarChamados(filtro, id):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            if filtro == "item":
            
                query = """
                    SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    WHERE c.idItem = %s
                    ORDER BY c.dataChamado DESC
                """
                cursor.execute(query, (id,))
                chamados = cursor.fetchall()

                query_item = "SELECT nomeItem FROM item WHERE idItem = %s"
                cursor.execute(query_item, (id,))
                nomeItem = cursor.fetchone()

                title = "Chamados por item: " + nomeItem
            
            elif filtro == "local":

                query = """
                    SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    WHERE c.idLocal = %s
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (id,))
                chamados = cursor.fetchall()

                query_local = "SELECT nomeLocal FROM local WHERE idLocal = %s"
                cursor.execute(query_local, (id,))
                nomeLocal = cursor.fetchone()

                title = "Chamados por Local: " + nomeLocal
            
            elif filtro == "status":

                query = """
                    SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    WHERE c.idStatus = %s
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (id,))
                chamados = cursor.fetchall()

                if id == 1:
                    title = "Chamados Não Respondidos"
                elif id == 2:
                    title = "Chamados Respondidos"
                else:
                    title = "Chamados Concluídos"

            elif filtro == "usuario":

                query = """
                    SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    WHERE c.idUsuario = %s
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (id,))
                chamados = cursor.fetchall()

                title = "Meus chamados"
            # Agrupar chamados por data
            chamados_por_data = {}
            for chamado in chamados:
                data = chamado['dataChamado'].strftime("%a, %d de %B")
                if data not in chamados_por_data:
                    chamados_por_data[data] = []
                chamados_por_data[data].append(chamado)

            return render_template(
                "listaChamado.html",
                chamados_por_data=chamados_por_data,
                title=title,
                login=True
            )
        finally:
            conexao.close()
    else:
        return redirect("/login")


# seleção dos blocos para o chamado por sala
@adm_blueprint.route("/chamSalasBloco")
def ChamBloco():
    title = "Chamados Por Bloco"
    
    # Conexão com o banco de dados
    conexao = conecta_database()
    cursor = conexao.cursor()

    # Executando os SELECTs necessários
    try:
        # SELECT para buscar apenas os nomes das áreas
        cursor.execute("SELECT nomeArea FROM area")
        areas = cursor.fetchall()

        # SELECT para buscar apenas os nomes dos locais
        cursor.execute("SELECT nomeLocal, idCategoria FROM local")
        locais = cursor.fetchall()

        # SELECT para buscar apenas os nomes das categorias
        cursor.execute("SELECT nomeCategoria FROM Categoria")
        categorias = cursor.fetchall()

        # Fechar a conexão após as operações
        conexao.close()

    except Exception as e:
        print(f"Erro ao executar SELECTs: {e}")
        conexao.close()
        return f"Erro ao carregar dados: {e}", 500

    # Renderizar template com os dados
    return render_template(
        "chamSalasBloco.html",
        title=title,
        login=True,
        areas=areas,
        locais=locais,
        categorias=categorias
    )



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
                os.remove(os.path.join("src/img/chamados", chamado['imgChamado']))
            except FileNotFoundError:
                pass  # Se o arquivo não for encontrado, continuamos sem falhar

        # Excluindo o chamado do banco de dados
        cursor.execute('DELETE FROM chamado WHERE idChamado = %s', (idChamado,))
        conexao.commit()
        conexao.close()

        return redirect('/adm')
    else:
        return redirect("/login")



# Dicionários para formatação
dias_da_semana = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

@adm_blueprint.app_template_filter('admData')
def data_formatada(data):
    if isinstance(data, str):
        if data == 'Data não disponível':
            return data
        try:
            data_datetime = datetime.strptime(data, "%Y-%m-%d")  # Verifica se a data está no formato esperado
        except ValueError:
            return 'Data inválida'  # Retorna "Data inválida" se a conversão falhar
    elif isinstance(data, datetime):
        data_datetime = data
    else:
        return 'Formato de data incorreto'  # Mensagem clara para valores de data inesperados
    
    dia_semana = dias_da_semana[data_datetime.weekday()]
    dia = data_datetime.day
    mes = meses[data_datetime.month]

    return f"{dia_semana}, {dia} de {mes}"


#Salvar foto do Usuario
@adm_blueprint.route('/img/usuarios/<path:filename>')
def serve_imageUser(filename):
    image_path = os.path.join(IMG_FOLDER, 'usuarios', filename)
    if os.path.exists(image_path):
        return send_from_directory(os.path.join(IMG_FOLDER, 'usuarios'), filename)
    else:
        return send_from_directory(os.path.join(IMG_FOLDER, 'usuarios'), 'userPlaceHolder.png')
    
#Salvar foto do Chamado
@adm_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    image_path = os.path.join(IMG_FOLDER, 'chamados', filename)
    if os.path.exists(image_path):
        return send_from_directory(os.path.join(IMG_FOLDER, 'chamados'), filename)
    else:
        return send_from_directory(os.path.join(IMG_FOLDER, 'chamados'), 'ImagemIcon.png')
    
#Salvar foto do App
@adm_blueprint.route('/img/app/<path:filename>')
def serve_imageApp(filename):
    image_path = os.path.join(IMG_FOLDER, 'app', filename)
    if os.path.exists(image_path):
        return send_from_directory(os.path.join(IMG_FOLDER, 'app'), filename)
