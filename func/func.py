from flask import render_template, Blueprint, redirect, send_from_directory, request, session, flash, url_for, jsonify
from session.session import verifica_sessao
from connection.connection import conecta_database  # Importando corretamente
import os, uuid
from datetime import datetime

func_blueprint = Blueprint("func", __name__, template_folder="templates")

IMG_FOLDER = os.path.join('src', 'img')

# Rota para a página inicial dos funcionários
@func_blueprint.route('/funcHome')
def func_home():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Obter o idUsuario da sessão
            id_usuario = session.get('idUsuario')
            if id_usuario is None:
                flash('Você precisa estar logado para visualizar os chamados!', 'error')
                return redirect('/login')

            # Modificar a consulta para incluir o idUsuario
            query = """
                SELECT c.descChamado, c.dataChamado, c.concChamado, l.nomeLocal, i.nomeItem, c.imgChamado, 
                       s.nomeStatus, c.idChamado, r.dataResposta
                FROM chamado c
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                LEFT JOIN resposta r ON c.idChamado = r.idChamado  
                WHERE c.idUsuario = %s
            """
            cursor.execute(query, (id_usuario,))
            chamados = cursor.fetchall()
            title = "Manutenção"

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
                    SELECT c.descChamado, c.concChamado, c.imgChamado, l.nomeLocal, i.nomeItem, s.nomeStatus
                    FROM chamado c
                    JOIN local l ON c.idLocal = l.idLocal
                    JOIN item i ON c.idItem = i.idItem
                    JOIN status s ON c.idStatus = s.idStatus
                    WHERE c.idChamado = %s
                """
                cursor.execute(query, (idChamado,))
                chamado = cursor.fetchone()

                queryResposta = """
                    SELECT r.descResposta, r.dataResposta, u.nomeUsuario
                    FROM resposta r
                    JOIN usuario u ON r.idUsuario = u.idUsuario
                    WHERE r.idChamado = %s
                """
                cursor.execute(queryResposta, (idChamado,))
                respostas = cursor.fetchall()
                title = "Detalhes do Chamado"
                return render_template('details.html', title=title, chamado=chamado, respostas=respostas, login=True)
            finally:
                 conexao.close()
        else:
            return redirect("/login")
        

# Rota para novoChamado
@func_blueprint.route("/novoChamado", methods=['GET', 'POST'])
def novoChamado():
    login = verifica_sessao()

    try:
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)

        if request.method == 'POST':
            # Obter o idUsuario da sessão
            id_usuario = session.get('idUsuario')
            if id_usuario is None:
                flash('Você precisa estar logado para cadastrar um chamado!', 'error')
                return redirect('/login')

            # Obter os dados do formulário
            area = request.form.get('area')
            local = request.form.get('local')
            item = request.form.get('item')
            descricao = request.form.get('descricao')
            imagem = request.files.get('imagem')        

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
            return redirect(url_for('func.func_home'))  # Corrigido para a rota de redirecionamento

        # Obtenção dos dados para o formulário
        cursor.execute('SELECT * FROM local')
        locais = cursor.fetchall()

        cursor.execute('SELECT * FROM item')
        itens = cursor.fetchall()

        cursor.execute("SELECT idArea, nomeArea FROM area")
        areas = cursor.fetchall()
        
        title = "Novo Chamado"
        return render_template("novoCham.html", title=title, login=login, locais=locais, itens=itens, areas=areas)

    finally:
        conexao.close()



@func_blueprint.route("/filtrarLocais/<int:idArea>", methods=['GET'])
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


@func_blueprint.route("/filtrarItens/<int:idLocal>", methods=['GET'])
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

# Rota do perfil do funcionário
@func_blueprint.route("/Perfil_funcionario", methods=['POST'])
def perfil_func():
    # Implementar lógica da tela de perfil
    pass


# Dicionários para formatação
dias_da_semana = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

@func_blueprint.app_template_filter('funcData')  # Use app_template_filter para registrar no Blueprint
def data_formatada(data):
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


# Rota para verificar a imagem do chamado
@func_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    # Caminho completo para a imagem
    image_path = os.path.join(IMG_FOLDER, 'chamados', filename)
    
    # Verifica se a imagem existe
    if os.path.exists(image_path):
        return send_from_directory(os.path.join(IMG_FOLDER, 'chamados'), filename)
    else:
        # Se não existir, retorna a imagem placeholder
        return send_from_directory(os.path.join(IMG_FOLDER, 'chamados'), 'ImagemIcon.png')

