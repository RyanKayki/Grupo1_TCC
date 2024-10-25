from flask import render_template, Blueprint, redirect, send_from_directory, request, session, flash, url_for
from session.session import verifica_sessao
from connection.connection import conecta_database  # Importando corretamente
import os, uuid

func_blueprint = Blueprint("func", __name__, template_folder="templates")

IMG_FOLDER = os.path.join('src', 'img')

# Rota para a página inicial dos funcionários
@func_blueprint.route('/funcHome')
def func_home():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            query = """
                SELECT c.descChamado, c.dataChamado, c.concChamado, l.nomeLocal, i.nomeItem, c.imgChamado, 
                       s.nomeStatus, c.idChamado, r.dataResposta
                FROM chamado c
                JOIN local l ON c.idLocal = l.idLocal
                JOIN item i ON c.idItem = i.idItem
                JOIN status s ON c.idStatus = s.idStatus
                LEFT JOIN resposta r ON c.idChamado = r.idChamado  -- Junção à tabela resposta
            """
            cursor.execute(query)
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
            id_usuario = session.get('idUsuario')  # Usando get() para evitar KeyError
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
                return redirect('/novoChamado')

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
            return redirect(url_for('func.home'))  # Altere para o redirecionamento desejado

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

# Rota para verficar imagem do chamado
@func_blueprint.route('/img/chamados/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(IMG_FOLDER, 'chamados'), filename)

