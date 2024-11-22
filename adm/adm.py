from flask import render_template, redirect, Blueprint, request, flash, url_for, session, jsonify, send_from_directory
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import uuid
from datetime import datetime
import ast # Biblioteca para converter string em dicionário
from collections import defaultdict # permite renderizar o ano apenas uma vez quando o ano muda.
from werkzeug.utils import secure_filename

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
                SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
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


# Rota para apagar um chamado
@adm_blueprint.route('/apagarChamado/<int:idChamado>', methods=['DELETE'])
def apagar_chamado(idChamado):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor()
            
            # Executa a exclusão do chamado pelo idChamado
            cursor.execute("DELETE FROM chamado WHERE idChamado = %s", (idChamado,))
            conexao.commit()
            
            return jsonify({"message": "Chamado apagado com sucesso."}), 200
        except Exception as e:
            return jsonify({"message": "Erro ao apagar o chamado.", "error": str(e)}), 500
        finally:
            conexao.close()
    else:
        return jsonify({"message": "Usuário não autenticado."}), 401


# Rota para exibir o formulário de edição de um chamado
@adm_blueprint.route('/editarChamado/<int:idChamado>', methods=['GET', 'POST'])
def editar_chamado(idChamado):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Carregar o chamado que será editado
            cursor.execute("SELECT * FROM chamado WHERE idChamado = %s", (idChamado,))
            chamado = cursor.fetchone()

            # Carregar dados adicionais, como áreas, locais e itens
            cursor.execute("SELECT * FROM local")
            locais = cursor.fetchall()

            cursor.execute("SELECT * FROM item")
            itens = cursor.fetchall()

            if request.method == 'POST':
                novo_desc = request.form.get('descricao')
                novo_local = request.form.get('local')
                novo_item = request.form.get('item')

                # Atualizar os dados do chamado
                cursor.execute("""
                    UPDATE chamado
                    SET descChamado = %s, idItem = %s, idLocal = %s
                    WHERE idChamado = %s
                """, (novo_desc, novo_item, novo_local, idChamado))

                conexao.commit()
                flash('Chamado atualizado com sucesso!', 'success')
                return redirect(url_for('adm.adm'))

            return render_template('editarChamados.html', chamado=chamado, locais=locais, itens=itens)

        finally:
            conexao.close()
    else:
        return redirect(url_for('login'))


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
@adm_blueprint.route("/chamadoSalas/<int:idArea>", methods=['GET'])
def chamadoSalas(idArea):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    query = """
    SELECT c.nomeCategoria, GROUP_CONCAT(l.nomeLocal SEPARATOR ', ') AS listaLocais
    FROM categoria c
    JOIN local l ON c.idCategoria = l.idCategoria
    WHERE l.idArea = %s
    GROUP BY c.nomeCategoria;
    """

    cursor.execute(query, (idArea,))
    locais = cursor.fetchall()
    
    if not locais:
        flash(f"Nenhum local encontrado nessa área.", "info")

    resultados = []
    for local in locais:  
            print(local)      
            lista_locais = local['listaLocais']
            lista_locais = lista_locais.split(", ")
            resultados.append({
                'nomeCategoria': local['nomeCategoria'],
                'listaLocais': lista_locais
            })
    query = """
    SELECT idArea, nomeArea FROM area WHERE idArea = %s
    """

    cursor.execute(query, (idArea,))
    area = cursor.fetchone()
    conexao.close()

    return render_template("chamadoSalas.html", title="Lista de salas", locais=resultados, area=area, login=True)

@adm_blueprint.route("/chamadosItens", methods=['GET'])
def chamadosItens():
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    query = """
    SELECT nomeItem FROM item
    """

    cursor.execute(query)
    itens = cursor.fetchall()
    if not itens:
        flash(f"Nenhum item encontrado.", "info")

    conexao.close()

    return render_template("chamadosItens.html", title="Lista de salas", itens=itens, login=True)

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
@adm_blueprint.route("/perfil", methods=["GET", "POST"])
def perfil():
    if verifica_sessao():
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)

        if request.method == "POST":
            # Processar atualização da foto de perfil
            nova_foto = request.files.get("fotoPerfil")
            if nova_foto and nova_foto.filename:
                # Buscar a foto atual do perfil
                cursor.execute('SELECT imgUsuario FROM usuario WHERE idUsuario = %s', (session['idUsuario'],))
                usuario = cursor.fetchone()

                # Excluir a foto antiga
                if usuario and usuario['imgUsuario']:
                    try:
                        os.remove(os.path.join("src/img/usuarios", usuario['imgUsuario']))
                    except FileNotFoundError:
                        pass  # Continua mesmo se o arquivo não existir

                # Salvar a nova foto
                nome_foto = f"{session['idUsuario']}_{secure_filename(nova_foto.filename)}"
                caminho_foto = os.path.join("src/img/usuarios", nome_foto)
                nova_foto.save(caminho_foto)

                # Atualizar o banco de dados com o novo caminho da foto
                cursor.execute('UPDATE usuario SET imgUsuario = %s WHERE idUsuario = %s', (nome_foto, session['idUsuario']))
                conexao.commit()

            conexao.close()
            return redirect("/perfil")

        elif request.method == "GET":
            # Buscar dados do perfil para exibir
            cursor.execute('SELECT u.nomeUsuario, u.emailUsuario, u.numeroUsuario, u.imgUsuario, u.senhaUsuario, c.nomeCargo FROM usuario u LEFT JOIN cargo c ON u.idCargo = c.idCargo WHERE idUsuario = %s', (session['idUsuario'],))
            usuario = cursor.fetchone()
            conexao.close()
            return render_template("perfil.html", usuario=usuario, login=True)

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


# Rota para editar um item específico
@adm_blueprint.route("/edicaoItem/<int:id_item>")
def edicaoItem(id_item):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Obter os detalhes do item específico
        query_item = "SELECT * FROM item WHERE idItem = %s"
        cursor.execute(query_item, (id_item,))
        item = cursor.fetchone()

        # Obter todas as categorias disponíveis
        query_categorias = "SELECT * FROM categoria"
        cursor.execute(query_categorias)
        categorias = cursor.fetchall()

        # Obter as categorias associadas ao item
        query_categorias_item = "SELECT idCategoria FROM item_categoria WHERE idItem = %s"
        cursor.execute(query_categorias_item, (id_item,))
        categorias_item = [categoria['idCategoria'] for categoria in cursor.fetchall()]

    finally:
        conexao.close()

    title = "Edição de Item"
    return render_template("edicaoItem.html", title=title, item=item, categorias=categorias, categorias_item=categorias_item, login=True)


# Rota para filtrarLocaledicao
@adm_blueprint.route("/filtrarLocaledicao", methods=["GET", "POST"])
def filtrarLocaledicao():
    # Conectar ao banco de dados
    conn = conecta_database()
    cursor = conn.cursor()

    # Capturar parâmetros de filtro da requisição
    filtro_area = request.args.get("area")
    filtro_categoria = request.args.get("categoria")

    # Consultar dados das áreas
    cursor.execute("SELECT idArea, nomeArea FROM `area`")
    salas = cursor.fetchall()

    # Consultar dados das categorias
    cursor.execute("SELECT idCategoria, nomeCategoria FROM `categoria`")
    categorias = cursor.fetchall()

    # Construir consulta SQL para locais com base nos filtros
    query = "SELECT idLocal, nomeLocal FROM local WHERE 1=1"  # Inicia a query
    params = []

    if filtro_area:
        query += " AND idArea = %s"
        params.append(filtro_area)

    if filtro_categoria:
        query += " AND idCategoria = %s"
        params.append(filtro_categoria)

    cursor.execute(query, params)
    locais_filtrados = cursor.fetchall()

    # Fechar conexão
    cursor.close()
    conn.close()

    # Renderizar o template passando os locais, categorias e resultados filtrados
    title = "Filtrar Local Edição"
    return render_template("filtrarLocaledicao.html", title=title, login=True, salas=salas, categorias=categorias, locais=locais_filtrados)



@adm_blueprint.route("/edicaoLocal/<int:id_local>")
def edicaoLocal(id_local):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Obter detalhes do local específico
        query_local = "SELECT * FROM `local` WHERE idLocal = %s"
        cursor.execute(query_local, (id_local,))
        local = cursor.fetchone()

        # Obter todas as categorias disponíveis
        query_categorias = "SELECT * FROM categoria"
        cursor.execute(query_categorias)
        categorias = cursor.fetchall()

        # Obter todas as áreas
        query_areas = "SELECT * FROM area"
        cursor.execute(query_areas)
        areas = cursor.fetchall()

        # Obter os itens presentes no local
        query_itens = """
            SELECT item.nomeItem FROM item
            JOIN item_categoria ON item.idItem = item_categoria.idItem
            WHERE item_categoria.idCategoria = %s
        """
        cursor.execute(query_itens, (local['idCategoria'],))
        itens = cursor.fetchall()

    finally:
        conexao.close()

    title = "Edição de Local"
    return render_template("edicaoLocal.html", title=title, local=local, areas=areas, categorias=categorias, itens=itens, login=True)


@adm_blueprint.route("/updateLocal/<int:id_local>", methods=['GET', 'POST'])
def updateLocal(id_local):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    try:
        # Busca todas as categorias e áreas disponíveis
        cursor.execute('SELECT * FROM categoria')
        categorias = cursor.fetchall()

        cursor.execute('SELECT * FROM area')
        areas = cursor.fetchall()

        # Identifica o ID do local para edição
        if not id_local:
            flash('Local não encontrado para edição.', 'error')
            return redirect(url_for('adm.adm'))

        # Busca os dados do local
        cursor.execute('SELECT * FROM local WHERE idLocal = %s', (id_local,))
        local = cursor.fetchone()

        # Busca os itens associados à categoria do local
        cursor.execute("""
            SELECT item.* FROM item
            JOIN item_categoria ON item.idItem = item_categoria.idItem
            WHERE item_categoria.idCategoria = %s
        """, (local['idCategoria'],))
        itens = cursor.fetchall()

        if request.method == 'POST':
            nome_sala = request.form.get("nome_sala")
            bloco = request.form.get("bloco")
            categorias_selecionadas = request.form.getlist('categorias')

            # Atualiza o local na tabela 'local'
            cursor.execute("UPDATE local SET nomeLocal = %s, idArea = %s WHERE idLocal = %s", (nome_sala, bloco, id_local))

            cursor.execute("UPDATE local SET idCategoria = %s WHERE idLocal = %s", (categorias_selecionadas[0], id_local))

            conexao.commit()
            flash('Local atualizado com sucesso!', 'success')
            return redirect(url_for('adm.adm'))  # Redireciona para a página de administração

    except Exception as e:
        flash(f'Erro ao atualizar local: {str(e)}', 'error')
        return redirect(url_for('adm.adm'))

    finally:
        conexao.close()

    return render_template("updateLocal.html", title="Editar Local", local=local, categorias=categorias, areas=areas, itens=itens, login=True)



@adm_blueprint.route("/chamadosBlocos")
def ChamBloco():
    title = "Selecione o bloco"
    return render_template("chamadosBlocos.html", title=title, login=True)

@adm_blueprint.route("/chamadoDetalhes/<int:id_chamado>")
def DetalheChamado(id_chamado):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Consulta para pegar os detalhes do chamado
            query_chamado = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus, c.idChamado
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                WHERE c.idChamado = %s
            """
            cursor.execute(query_chamado, (id_chamado,))
            chamado = cursor.fetchone()

            # Consulta para pegar as respostas associadas ao chamado
            query_respostas = """
                    SELECT r.descResposta, r.dataResposta, u.nomeUsuario
                    FROM resposta r
                    JOIN usuario u ON r.idUsuario = u.idUsuario
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
                SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, c.concChamado, s.nomeStatus,u.idUsuario, r.dataResposta
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                LEFT JOIN resposta r ON r.idChamado = c.idChamado
                ORDER BY c.dataChamado DESC          
            """
            cursor.execute(query)
            chamados = cursor.fetchall()
            title = "Registro de Chamados"
            titulo_pagina = "Registro de Chamados"

            idUsuario_logado = session.get("idUsuario")
            
            # Organizando por ano e data formatada (sem o ano na chave de data)
            chamados_por_ano = defaultdict(lambda: defaultdict(list))

            # Verifica se há chamados para o usuário logado
            if not chamados:
                flash("Nenhum chamado cadastrado no momento.", "info")
                return render_template("listaChamados.html", chamados_por_ano={}, title=title, titulo_pagina=titulo_pagina,idUsuario_logado=idUsuario_logado, login=True)


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

            return render_template("listaChamados.html", chamados_por_ano=chamados_por_ano, titulo_pagina=titulo_pagina, idUsuario_logado=idUsuario_logado, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")


# Filtragem dos chamados por status, item, local ou chamados do usuário
@adm_blueprint.route("/filtrarChamados/<filtro>/<valor>")
def filtrarChamados(filtro, valor):
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)
            idUsuario_logado = session.get("idUsuario")

            if filtro == "item":
            
                query = """
                    SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, c.concChamado, s.nomeStatus, r.dataResposta, c.idUsuario
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    LEFT JOIN resposta r ON r.idChamado = c.idChamado
                    WHERE c.idItem = (SELECT idItem FROM item WHERE nomeItem = %s)
                    ORDER BY c.dataChamado DESC
                """
                cursor.execute(query, (valor,))
                chamados = cursor.fetchall()

                title = "Chamados por item: " + valor
            
            elif filtro == "local":

                query = """
                    SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, c.concChamado, s.nomeStatus, r.dataResposta, c.idUsuario
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    LEFT JOIN resposta r ON r.idChamado = c.idChamado
                    WHERE c.idLocal = (SELECT idLocal FROM local WHERE nomeLocal = %s)
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (valor,))
                chamados = cursor.fetchall()

                title = "Chamados por Local: " + valor
            
            elif filtro == "status":

                query = """
                    SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, c.concChamado, s.nomeStatus, r.dataResposta, c.idUsuario
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    LEFT JOIN resposta r ON r.idChamado = c.idChamado
                    WHERE c.idStatus = %s
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (valor,))
                chamados = cursor.fetchall()

                if valor == "1":
                    title = "Chamados Não Respondidos"
                elif valor == "2":
                    title = "Chamados Respondidos"
                else:
                    title = "Chamados Concluídos"

            elif filtro == "usuario":
                # Obtém o ID do usuário logado
                valor = session.get('idUsuario')
                
                query = """
                    SELECT c.idChamado, c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, c.concChamado, s.nomeStatus, r.dataResposta, c.idUsuario
                    FROM chamado c
                    JOIN usuario u ON c.idUsuario = u.idUsuario
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    LEFT JOIN resposta r ON r.idChamado = c.idChamado
                    WHERE c.idUsuario = %s
                    ORDER BY c.dataChamado DESC
                """ 

                cursor.execute(query, (valor,))
                chamados = cursor.fetchall()
                
                title = "Meus chamados"


            # Organizando por ano e data formatada (sem o ano na chave de data)
            chamados_por_ano = defaultdict(lambda: defaultdict(list))

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

            if not chamados:
                flash(f"Nenhum chamado encontrado.", "info")
                chamados_por_ano = {}

            return render_template("listaChamados.html", chamados_por_ano=chamados_por_ano, idUsuario_logado=idUsuario_logado, title=title, login=True)
        finally:
            conexao.close()
    else:
        return redirect("/login")


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


@adm_blueprint.app_template_filter('admCardData')  # Use app_template_filter para registrar no Blueprint
def data_formatada_card(data):
    if isinstance(data, str):
        if data == 'Data não disponível':
            return data  # Retorna a mensagem diretamente
        try:
            data_datetime = datetime.strptime(data, "%Y-%m-%d")  # Converte para datetime
        except ValueError:
            return 'Data inválida'  # Retorna uma mensagem de erro caso a conversão falhe
    else:
        data_datetime = data

    # Formata a data como xx/xx/xx às xx:xx
    return data_datetime.strftime("%d/%m/%y às %H:%M")
################### PESQUISAS ###############################
#Função de pesquisar locais
@adm_blueprint.route('/pesquisaLocal/<idArea>', methods=['POST'])
def pesquisaLocal(idArea):
    termo = request.form.get('termo')
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    query = """
        SELECT c.nomeCategoria, GROUP_CONCAT(l.nomeLocal SEPARATOR ', ') AS listaLocais
        FROM categoria c
        JOIN local l ON c.idCategoria = l.idCategoria
        WHERE l.nomeLocal LIKE %s AND l.idArea = %s
        GROUP BY c.nomeCategoria;
    """
    # Adiciona '%' ao redor do termo para realizar a busca com LIKE
    cursor.execute(query, ('%' + termo + '%', idArea,))
    locais = cursor.fetchall()
    
    if not locais:
        flash(f"Nenhum local encontrado nessa área.", "info")

    resultados = []
    for local in locais:
        lista_locais = local['listaLocais'].split(", ")
        resultados.append({
            'nomeCategoria': local['nomeCategoria'],
            'listaLocais': lista_locais
        })

    query = """
    SELECT idArea, nomeArea FROM area WHERE idArea = %s
    """

    cursor.execute(query, (idArea,))
    area = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template("chamadoSalas.html", title="Lista de salas", locais=resultados, area=area, login=True)


#Função de pesquisar item
@adm_blueprint.route('/pesquisaItem', methods=['POST'])
def pesquisa():
    termo = request.form.get('termo')
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    query = """
        SELECT i.idItem, i.nomeItem
        FROM item i
        WHERE i.nomeItem LIKE %s;
        """
    
    # Adiciona '%' ao redor do termo para realizar a busca com LIKE
    cursor.execute(query, ('%' + termo + '%',))
    itens = cursor.fetchall()

    if not itens:
        flash(f"Nenhum item encontrado.", "info")
    
    return render_template("chamadosItens.html", title="Lista de salas", itens=itens, login=True)


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
