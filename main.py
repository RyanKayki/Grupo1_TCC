from flask import Flask, render_template, request, redirect, session
import mysql.connector
import uuid, os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = "Rhzin"

usuario = "rh"
senha = "rh"
login = False

def verifica_sessao():
    return "login" in session and session["login"]

def conecta_database():
    conexao = mysql.connector.connect(
        host='localhost',
        user='root', 
        password='senai',
        database='tcc'
    )
    return conexao

def iniciar_db():
    conexao = conecta_database()
    cursor = conexao.cursor()
    with app.open_resource('esquema.sql', mode='r') as comandos:
        cursor.execute(comandos.read(), multi=True)
    conexao.commit()
    conexao.close()

@app.route('/')
def index():
    iniciar_db()
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM chamados ORDER BY id_chamado DESC')
    chamados = cursor.fetchall()
    title = "Fale Conosco"
    login = verifica_sessao()
    return render_template("home.html", chamados=chamados, login=login, title=title)

@app.route("/cadastro")
def cadastros():
    login = verifica_sessao()
    if login:
        title = "Cadastro"
        return render_template("cadastro.html", title=title, login=login)
    else:
        return redirect("/login")

@app.route("/cadchamados")
def cadchamado():
    login = verifica_sessao()
    if login:
        title = "Cadastro de Chamados"
        return render_template("cadchamados.html", title=title, login=login)
    else:
        return redirect("/login")

@app.route('/somos')
def somos():
    title = "Sobre"
    login = verifica_sessao()
    return render_template("somos.html", title=title, login=login)

@app.route('/politica')
def politica():
    title = "Privacidade"
    login = verifica_sessao()
    return render_template("privacidade.html", title=title, login=login)

@app.route('/curriculo')
def curriculo():
    title = "Currículo"
    login = verifica_sessao()
    return render_template("curriculo.html", title=title, login=login)

@app.route('/termo')
def termo():
    title = "Termo De Uso"
    login = verifica_sessao()
    return render_template("termo.html", title=title, login=login)

@app.route('/troca')
def troca():
    title = "Trocas e Devoluções"
    login = verifica_sessao()
    return render_template("troca.html", title=title, login=login)

@app.route("/vermais/<int:id_chamado>")
def sobre(id_chamado):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chamados WHERE id_chamado = %s", (id_chamado,))
    chamado = cursor.fetchall()
    conexao.close()
    title = "Ver Mais"
    return render_template("vermais.html", title=title, chamado=chamado)

@app.route("/upload", methods=["POST"])
def upload():
    if 'pdf_file' in request.files:
        cargo_chamado = request.form['cargo_chamado']
        id_pdf = str(uuid.uuid4().hex)
        filename = id_pdf + cargo_chamado + '.pdf'
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chamados WHERE id_chamado = %s", (cargo_chamado,))
        pdf_chamado = request.files['pdf_file']
        if pdf_chamado.filename == '':
            return 'Nenhum arquivo selecionado.'
        else:
            pdf_chamado.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'Arquivo enviado com sucesso!'
    else:
        return 'Nenhum arquivo enviado.'

@app.route("/cadastro_equipamento", methods=["POST"])
def cadastro_equipamento():
    if verifica_sessao():
        nome_produto = request.form['nome_produto']
        destinado_para = request.form['destinado_para']
        quantidade = request.form['quantidade']
        data_chegada = request.form['data_chegada']
        revisao_programada = request.form['revisao_programada']
        
        conexao = conecta_database()
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO equipamentos (nome_produto, destinado_para, quantidade, data_chegada, revisao_programada) VALUES (%s, %s, %s, %s, %s)', 
                       (nome_produto, destinado_para, quantidade, data_chegada, revisao_programada))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/cadastro_funcionario", methods=["POST"])
def cadastro_funcionario():
    if verifica_sessao():
        nome_completo = request.form['nome_completo']
        cargo = request.form['cargo']
        data_nascimento = request.form['data_nascimento']
        email = request.form['email']
        numero = request.form['numero']
        
        conexao = conecta_database()
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO funcionarios (nome_completo, cargo, data_nascimento, email, numero) VALUES (%s, %s, %s, %s, %s)', 
                       (nome_completo, cargo, data_nascimento, email, numero))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/cadastro_sala", methods=["POST"])
def cadastro_sala():
    if verifica_sessao():
        nome_sala = request.form['nome_sala']
        numero_sala = request.form['numero_sala']
        bloco = request.form['bloco']
        
        conexao = conecta_database()
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO salas (nome_sala, numero_sala, bloco) VALUES (%s, %s, %s)', 
                       (nome_sala, numero_sala, bloco))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/cadastro_chamado", methods=["POST"])
def cadastro_chamado():
    if verifica_sessao():
        cargo_chamado = request.form['cargo_chamado']
        local_chamado = request.form['local_chamado']
        descricao_chamado = request.form['descricao_chamado']
        img_chamado = request.files['img_chamado']
        
        # Gerar um nome único para o arquivo de imagem
        id_foto = str(uuid.uuid4().hex)
        filename = id_foto + ".png"
        img_chamado.save(os.path.join("static/img/chamados/", filename))
        
        # Inserir dados na tabela
        conexao = conecta_database()
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO chamados (cargo_chamado, local_chamado, descricao_chamado, img_chamado) VALUES (%s, %s, %s, %s)', 
                       (cargo_chamado, local_chamado, descricao_chamado, filename))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/adm")
def adm():
    if verifica_sessao():
        iniciar_db()
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscar chamados
        cursor.execute('SELECT * FROM chamados ORDER BY id_chamado DESC')
        chamados = cursor.fetchall()
        
        # Buscar equipamentos
        cursor.execute('SELECT * FROM equipamentos')
        equipamentos = cursor.fetchall()
        equipamentos_dict = {e['id_equipamento']: e for e in equipamentos}
        
        # Buscar salas
        cursor.execute('SELECT * FROM salas')
        salas = cursor.fetchall()
        salas_dict = {s['id_sala']: s for s in salas}
        
        conexao.close()
        
        title = "Administração"
        login = verifica_sessao()
        return render_template(
            "adm.html",
            chamados=chamados,
            equipamentos=equipamentos_dict,
            salas=salas_dict,
            title=title,
            login=login
        )
    else:
        return redirect("/login")


@app.route("/excluir/<int:id_chamado>")
def excluir(id_chamado):
    if verifica_sessao():
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute('SELECT img_chamado FROM chamados WHERE id_chamado = %s', (id_chamado,))
        chamado = cursor.fetchone()
        if chamado:
            os.remove(os.path.join("static/img/chamados/", chamado['img_chamado']))
        cursor.execute('DELETE FROM chamados WHERE id_chamado = %s', (id_chamado,))
        conexao.commit()
        conexao.close()
        return redirect('/adm')
    else:
        return redirect("/login")

@app.route('/login')
def login_page():
    title = "Login"
    return render_template("login.html", title=title)

@app.route("/acesso", methods=['POST'])
def acesso():
    global usuario, senha
    usuario_informado = request.form["usuario"]
    senha_informada = request.form["senha"]
    if usuario == usuario_informado and senha == senha_informada:
        session["login"] = True
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/logout")
def logout():
    session.pop("login")
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
