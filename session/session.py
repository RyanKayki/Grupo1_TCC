from flask import render_template, session, redirect, request, Flask, Blueprint, flash, make_response
import mysql.connector
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "Rhzin"

# Definindo o blueprint
session_blueprint = Blueprint("session", __name__, template_folder="templates", static_folder='src')


# Função para conectar ao banco de dados
def conecta_database():
    conexao = mysql.connector.connect(
        host='localhost',
        user='root',
        password='senai',
        database='tcc',
        port='3306'
    )
    return conexao


# Função para verificar sessão ou configurar a partir dos cookies
def verifica_sessao():
    if "login" in session and session["login"]:
        return True

    id_usuario = request.cookies.get('idUsuario')
    cargo = request.cookies.get('cargo')

    if id_usuario and cargo:
        session["login"] = True
        session["idUsuario"] = id_usuario
        session["cargo"] = cargo
        return True

    return False


# Rota inicial que redireciona com base no cargo do usuário
@session_blueprint.route('/')
def index():
    if verifica_sessao():
        cargo = session.get('cargo')
        if cargo == "Administração":
            return redirect("/adm")
        elif cargo == "Manutenção":
            return redirect("/tecHome")
        else:
            return redirect("/funcHome")
    return redirect("/login")


# Rota de login
@session_blueprint.route('/login')
def login_page():
    if verifica_sessao():
        cargo = session.get('cargo')
        if cargo == "Administração":
            return redirect("/adm")
        elif cargo == "Manutenção":
            return redirect("/tecHome")
        else:
            return redirect("/funcHome")
    return render_template("login.html", title="Login")


# Rota de acesso ao sistema
@session_blueprint.route("/acesso", methods=['POST'])
def acesso():
    email_informado = request.form["email"]
    senha_informada = request.form["senha"]
    lembrar = 'chklembrar' in request.form

    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute('SELECT * FROM usuario WHERE emailUsuario = %s', (email_informado,))
    email = cursor.fetchone()

    if email is None:
        flash("Email não cadastrado", "email")
        cursor.close()
        conexao.close()
        return redirect("/login")

    if not senha_informada:
        flash("Informe a senha", "senha")
        cursor.close()
        conexao.close()
        return redirect("/login")

    if email['senhaUsuario'] != senha_informada:
        flash("Senha incorreta", "senha")
        cursor.close()
        conexao.close()
        return redirect("/login")

    query = """
    SELECT c.nomeCargo, u.idUsuario
    FROM Cargo c
    JOIN usuario u ON c.idCargo = u.idCargo
    WHERE u.emailUsuario = %s
    """
    cursor.execute(query, (email_informado,))
    cargo_data = cursor.fetchone()

    if not cargo_data:
        flash("Erro ao recuperar cargo do usuário", "erro")
        cursor.close()
        conexao.close()
        return redirect("/login")

    session["login"] = True
    session["email"] = email_informado
    session["cargo"] = cargo_data["nomeCargo"]
    session["idUsuario"] = cargo_data["idUsuario"]

    resp = make_response(redirect("/"))

    # Configurando cookies para "Lembrar-me"
    if lembrar:
        resp.set_cookie('idUsuario', str(cargo_data["idUsuario"]), max_age=timedelta(days=30))
        resp.set_cookie('cargo', cargo_data["nomeCargo"], max_age=timedelta(days=30))

    cursor.close()
    conexao.close()
    return resp


# Rota para recuperação de senha
@session_blueprint.route('/recuperarsenha', methods=['GET', 'POST'])
def recuperarsenha():
    if request.method == 'POST':
        email = request.form.get('email')

        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        try:
            query = "SELECT nomeUsuario, senhaUsuario FROM usuario WHERE emailUsuario = %s"
            cursor.execute(query, (email,))
            usuario = cursor.fetchone()
        finally:
            cursor.close()
            conexao.close()

        if usuario:
            nome_usuario = usuario['nomeUsuario']
            senha = usuario['senhaUsuario']
            flash(f'Olá, {nome_usuario}. Sua senha é: {senha}', 'senha')
        else:
            flash('E-mail não encontrado.', 'senha')

        return redirect(request.url)

    return render_template("rememberPassword.html", title="Recuperar Senha")


# Rota para logout
@session_blueprint.route("/logout")
def logout():
    session.clear()
    resp = redirect("/login")
    resp.delete_cookie('idUsuario')
    resp.delete_cookie('cargo')
    return resp


# Registrando o blueprint no app
app.register_blueprint(session_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
