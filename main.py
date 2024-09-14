from flask import Flask, render_template, request, redirect, session
import sqlite3 as sql
import uuid, os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = "Rhzin"

usuario = "rh"
senha = "rh"
login = False

def verifica_sessao():
    if "login" in session and session["login"]:
        return True
    else:
        return False

def conecta_database():
    conexao = sql.connect("youtech.db")
    conexao.row_factory = sql.Row
    return conexao

def iniciar_db():
    conexao = conecta_database()
    with app.open_resource('esquema.sql', mode='r') as comandos:
        conexao.cursor().executescript(comandos.read())
    conexao.commit()
    conexao.close()

@app.route('/')
def index():
    iniciar_db()
    conexao = conecta_database()
    chamados = conexao.execute('SELECT * FROM chamados ORDER BY id_chamado DESC').fetchall()
    title = "Fale Conosco"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("home.html", chamados=chamados, login=login, title=title)

@app.route("/cadchamados")
def cadchamados():
    if verifica_sessao():
        login = True
    else:
        login = False
    if verifica_sessao():
        title = "Cadastro de Chamados"
        return render_template("cadastro.html", title=title, login=login)
    else:
        return redirect("/login")

@app.route('/somos')
def somos():
    title = "Sobre"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("somos.html", title=title, login=login)

@app.route('/politica')
def politica():
    title = "Privacidade"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("privacidade.html", title=title, login=login)

@app.route('/curriculo')
def curriculo():
    title = "Currículo"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("curriculo.html", title=title, login=login)

@app.route('/termo')
def termo():
    title = "Termo De Uso"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("termo.html", title=title, login=login)

@app.route('/troca')
def troca():
    title = "Trocas e Devoluções"
    if verifica_sessao():
        login = True
    else:
        login = False
    return render_template("troca.html", title=title, login=login)

@app.route("/vermais/<id_chamado>")
def sobre(id_chamado):
    id_chamado = int(id_chamado)
    conexao = conecta_database()
    chamado = conexao.execute("SELECT * FROM chamados WHERE id_chamado = ?", (id_chamado,)).fetchall()
    conexao.close()
    title = "Ver Mais"
    print(chamado)
    return render_template("vermais.html", title=title, chamado=chamado)

@app.route("/upload", methods=["POST"])
def upload():
    if 'pdf_file' in request.files:
        cargo_chamado = request.form['cargo_chamado']
        id_pdf = str(uuid.uuid4().hex)
        filename = id_pdf + cargo_chamado + '.pdf'
        conexao = conecta_database()
        conexao.execute("SELECT * FROM chamados WHERE id_chamado = ?", (cargo_chamado,)).fetchall()
        pdf_chamado = request.files['pdf_file']
        if pdf_chamado.filename == '':
            return 'Nenhum arquivo selecionado.'
        else:
            pdf_chamado.save(r"static/upload/" + filename)
            return 'Arquivo enviado com sucesso!'
    else:
        return 'Nenhum arquivo enviado.'

@app.route("/cadastro", methods=["post"])
def cadastro():
    if verifica_sessao():
        cargo_chamado = request.form['cargo_chamado']
        local_chamado = request.form['local_chamado']
        descricao_chamado = request.form['descricao_chamado']
        img_chamado = request.files['img_chamado']
        id_foto = str(uuid.uuid4().hex)
        filename = id_foto + cargo_chamado + '.png'
        img_chamado.save("static/img/chamados/" + filename)
        conexao = conecta_database()
        conexao.execute('INSERT INTO chamados (cargo_chamado, local_chamado, descricao_chamado, img_chamado) VALUES (?,?,?,?)', 
                        (cargo_chamado, local_chamado, descricao_chamado, filename))
        conexao.commit()
        conexao.close()
        return redirect("/adm")
    else:
        return redirect("/login")

@app.route("/adm")
def adm():
    if verifica_sessao():
        login = True
    else:
        login = False
    if verifica_sessao():
        iniciar_db()
        conexao = conecta_database()
        chamados = conexao.execute('SELECT * FROM chamados ORDER BY id_chamado DESC').fetchall()
        conexao.close()
        title = "Administração"
        return render_template("adm.html", chamados=chamados, title=title, login=login)
    else:
        return redirect("/login")

@app.route("/excluir/<id_chamado>")
def excluir(id_chamado):
    if verifica_sessao():
        id_chamado = int(id_chamado)
        conexao = conecta_database()
        chamado = conexao.execute('SELECT img_chamado FROM chamados WHERE id_chamado = ?', (id_chamado,)).fetchone()
        filename_old = chamado[0]
        os.remove("static/img/chamados/" + filename_old)
        conexao.execute('DELETE FROM chamados WHERE id_chamado = ?', (id_chamado,))
        conexao.commit()
        conexao.close()
        return redirect('/adm')
    else:
        return redirect("/login")

@app.route('/login')
def login():
    title = "Login"
    return render_template("login.html", title=title)

@app.route("/acesso", methods=['post'])
def acesso():
    global usuario, senha
    usuario_informado = request.form["usuario"]
    senha_informada = request.form["senha"]
    if usuario == usuario_informado and senha == senha_informada:
        session["login"] = True
        return redirect('/adm')
    else:
        return render_template("login.html", msg="Usuário/Senha estão incorretos!")

@app.route("/logout")
def logout():
    global login
    login = False
    session.clear()
    return redirect("/")

@app.route("/editchamados/<id_chamado>")
def editar(id_chamado):
    if verifica_sessao():
        iniciar_db()
        conexao = conecta_database()
        chamados = conexao.execute('SELECT * FROM chamados WHERE id_chamado = ?', (id_chamado,)).fetchall()
        conexao.close()
        title = "Edição dos Chamados"
        return render_template("editchamados.html", chamados=chamados, title=title)
    else:
        return redirect("/login")

@app.route("/editarchamados", methods=['POST'])
def editpost():
    id_chamado = request.form['id_chamado']
    cargo_chamado = request.form['cargo_chamado']
    requisitos_chamado = request.form['requisitos_chamado']
    salario_chamado = request.form['salario_chamado']
    local_chamado = request.form['local_chamado']
    tipo_chamado = request.form['tipo_chamado']
    img_chamado = request.files['img_chamado']
    email_chamado = request.form['email_chamado']
    conexao = conecta_database()
    cursor = conexao.cursor()
    cursor.execute('SELECT img_chamado FROM chamados WHERE id_chamado = ?', (id_chamado,))
    result = cursor.fetchone()
    imagem_antiga = result[0] if result else None
    conexao.close()
    if img_chamado:
        id_foto = str(uuid.uuid4().hex)
        filename = id_foto + cargo_chamado + '.png'
        img_chamado.save("static/img/chamados/" + filename)
        if imagem_antiga:
            os.remove(os.path.join("static/img/chamados", imagem_antiga))
    else:
        filename = imagem_antiga
    conexao = conecta_database()
    conexao.execute(
        'UPDATE chamados SET cargo_chamado = ?, requisitos_chamado = ?, salario_chamado = ?, local_chamado = ?, img_chamado = ?, email_chamado = ?, tipo_chamado = ? WHERE id_chamado = ?',
        (cargo_chamado, requisitos_chamado, salario_chamado, local_chamado, filename, email_chamado, tipo_chamado, id_chamado)
    )
    conexao.commit()
    conexao.close()
    return redirect("/adm")

if __name__ == '__main__':
    app.run(debug=True)
