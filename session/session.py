from flask import render_template, session, redirect, request, Flask, Blueprint, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "Rhzin"

# Definindo o blueprint
session_blueprint = Blueprint("session", __name__, template_folder="templates", static_folder='src')

#DB CLOUD
def conecta_database():
    conexao = mysql.connector.connect(
        host='localhost',  # Host do Railway
        user='root',                     # Usuário do banco de dados
        password='senai',  # Senha do banco de dados
        database='tcc',              # Nome do banco de dados fornecido pelo Railway
        port='3306'                     # Porta do banco de dados no Railway
    )
    return conexao

def verifica_sessao():
    # Verifica se a sessão de login está ativa
    return "login" in session and session["login"]

@session_blueprint.route('/')
def index():
    # Rota inicial que redireciona baseado no cargo do usuário
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuario')
    conexao.close()

    login = verifica_sessao()
    if login:
        cargo = session['cargo']
        if cargo == "Administração":
            return redirect("/adm")
        elif cargo == "Manutenção":
            return redirect("/tecHome")
        else:
            return redirect("/funcHome")
    else:
        return redirect("/login")

@session_blueprint.route('/login')
def login_page():
    # Página de login
    title = "Login"
    return render_template("login.html", title=title)  # Exibe página de login caso não esteja logado

@session_blueprint.route("/acesso", methods=['POST'])
def acesso():
    # Validação de login
    usuario_informado = request.form["usuario"]
    senha_informada = request.form["senha"]

    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuario WHERE nomeUsuario = %s', (usuario_informado,))
    usuario = cursor.fetchone()
    cursor.close()  # Fechando o cursor

    if usuario is None:
        # Usuário não cadastrado
        flash("Usuário não cadastrado", "usuario")
        return redirect("/login")

    if not senha_informada:
        # Se a senha não for informada
        flash("Informe a senha", "senha")
        return redirect("/login")

    if usuario['senhaUsuario'] != senha_informada:
        # Senha incorreta
        flash("Senha incorreta", "senha")
        return redirect("/login")

    # Se as credenciais estiverem corretas
    cursor = conexao.cursor(dictionary=True)
    session["login"] = True
    session["usuario"] = usuario_informado
    print(usuario_informado)
    # Query para pegar o nome do cargo
    query = """
    SELECT c.nomeCargo
    FROM Cargo c
    JOIN usuario u ON c.idCargo = u.idCargo
    WHERE u.nomeUsuario = %s
"""

    cursor.execute(query, (usuario_informado,))
    nomeCargo = cursor.fetchall()

    if nomeCargo:
        print(nomeCargo[0]["nomeCargo"])
        session["cargo"] = nomeCargo[0]["nomeCargo"]  # Salvando o nome do cargo corretamente na sessão
    else:
        session["cargo"] = None
    cargo = session['cargo']
    cursor.close()  # Fechando o cursor
    conexao.close()

    # Redirecionando com base no cargo
    if cargo == "Administração":
            return redirect("/adm")
    elif cargo == "Manutenção":
        return redirect("/tecHome")
    else:
        return redirect("/funcHome")


# Rota para recuperação de senha
@session_blueprint.route('/recupsenha')
def recupsenha():
    title = "Recuperar Senha"
    login = verifica_sessao()
    return render_template("RecupSenha.html", title=title, login=login)

# Rota para código de recuperação de senha
@session_blueprint.route('/codigosenha')
def codigosenha():
    title = "Recuperar Senha"
    login = verifica_sessao()
    return render_template("CodigoSenha.html", title=title, login=login)

# Rota para exibir a senha recuperada
@session_blueprint.route('/mostrasenha')
def mostrasenha():
    title = "Recuperar Senha"
    login = verifica_sessao()
    return render_template("MostraSenha.html", title=title, login=login)


@session_blueprint.route("/logout")
def logout():
    # Encerrando sessão
    session.pop("login", None)
    session.pop("usuario", None)
    session.pop("cargo", None)
    return redirect("/login")

# Registrando o blueprint no app
app.register_blueprint(session_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
