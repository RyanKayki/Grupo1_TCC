from flask import render_template, redirect, Blueprint, request, flash, url_for, session, jsonify, send_from_directory
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import uuid
from datetime import datetime

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
                if not imagem:
                    flash('A imagem é obrigatória para cadastrar um chamado!', 'error')
                    return redirect('/cadchamados')

                # Gerar um nome único para a imagem
                id_foto = str(uuid.uuid4().hex)
                filename = f"{id_foto}_{item}.png"
                imagem.save(os.path.join("src/img/chamados", filename))  # Corrigido para o diretório correto

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


# Rota para cadUsuario
@adm_blueprint.route("/cadUsuario", methods=['GET', 'POST'])
def cadastroUsuario():
    if request.method == 'POST':
        # Obter os dados do formulário
        nome_completo = request.form.get('nome_completo')
        email = request.form.get('nome_email')
        cargo = request.form.get('cargo')
        numero = request.form.get('numero')

        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Inserindo o novo usuário no banco de dados
            cursor.execute("""
                INSERT INTO usuario (nomeUsuario, emailUsuario, idCargo, dataNascimento, numero)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome_completo, email, cargo,  numero))

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
    title = "Filtrar Local Edição"
    return render_template("filtrarLocaledicao.html", title=title, login=True)

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
    return render_template("chamadosSala.html", title=title, login=True)

# Registro de Chamados - Histórico de chamados agrupados por data
@adm_blueprint.route("/registroChamados")
def registroChamados():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Consulta para obter todos os chamados do usuário logado, agrupados por data
            query_chamados = """
                SELECT c.descChamado, c.dataChamado, u.nomeUsuario, l.nomeLocal, i.nomeItem, c.imgChamado, s.nomeStatus
                FROM chamado c
                JOIN usuario u ON c.idUsuario = u.idUsuario
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                ORDER BY c.dataChamado DESC
            """
            cursor.execute(query_chamados)
            chamados = cursor.fetchall()

            # Agrupar chamados por data
            chamados_por_data = {}
            for chamado in chamados:
                data = chamado['dataChamado'].strftime("%a, %d de %B")
                if data not in chamados_por_data:
                    chamados_por_data[data] = []
                chamados_por_data[data].append(chamado)

            return render_template(
                "registroCham.html",
                chamados_por_data=chamados_por_data,
                title="Registro de Chamados",
                login=True
            )
        finally:
            conexao.close()
    else:
        return redirect("/login")


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
dias_da_semana = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
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
    ano = data_datetime.year

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
    

