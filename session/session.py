from flask import render_template, session, redirect, request, Flask, Blueprint, flash
import mysql.connector
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "Rhzin"

# Definindo o blueprint
session_blueprint = Blueprint("session", __name__, template_folder="templates", static_folder='src')

#DB CLOUD
def conecta_database():
    conexao = mysql.connector.connect(
        host='localhost',  # Host do Railway
        user='root',                     # Usuário do banco de dados
        password='senai',  # Senha do banco de dado
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
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuario')
    conexao.close()
    title = "Login"
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
        return render_template("login.html", title=title)




@session_blueprint.route("/acesso", methods=['POST'])
def acesso():
    email_informado = request.form["email"]
    senha_informada = request.form["senha"]
    lembrar = 'chklembrar' in request.form

    # Conectando ao banco de dados
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

    session["login"] = True
    session["email"] = email_informado

    # Se "lembrar de mim" for marcado, define um cookie
    if lembrar:
        resp = redirect("/")
        resp.set_cookie('email', email_informado, max_age=timedelta(days=30))  # O cookie dura 30 dias
        return resp

    # Restante do código para carregar cargo do usuário
    query = """
    SELECT c.nomeCargo, u.idUsuario
    FROM Cargo c
    JOIN usuario u ON c.idCargo = u.idCargo
    WHERE u.emailUsuario = %s
    """
    cursor.execute(query, (email_informado,))
    cargo_data = cursor.fetchone()

    if cargo_data:
        session["cargo"] = cargo_data["nomeCargo"]
        session["idUsuario"] = cargo_data["idUsuario"]
    
    cursor.close()
    conexao.close()

    if session["cargo"] == "Administração":
        return redirect("/adm")
    elif session["cargo"] == "Manutenção":
        return redirect("/tecHome")
    else:
        return redirect("/funcHome")




# Rota para exibir a senha recuperada
@session_blueprint.route('/recuperarsenha', methods=['GET', 'POST'])
def recuperarsenha():
    if request.method == 'POST':
        email = request.form.get('email')

        # Conectando ao banco de dados e buscando a senha
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        try:
            query = "SELECT nomeUsuario, senhaUsuario FROM usuario WHERE emailUsuario = %s"
            cursor.execute(query, (email,))
            usuario = cursor.fetchone()
        finally:
            cursor.close()
            conexao.close()

        # Verificando se o e-mail foi encontrado
        if usuario:
            nome_usuario = usuario['nomeUsuario']
            senha = usuario['senhaUsuario']
            flash(f'Olá, {nome_usuario}. Sua senha é: {senha}', 'senha')  # Categoria "senha"
        else:
            flash('E-mail não encontrado.', 'senha')

        return redirect(request.url)

    title = "Recuperar Senha"
    return render_template("rememberPassword.html", title=title)



@session_blueprint.route("/logout")
def logout():
    session.pop("login", None)
    session.pop("usuario", None)
    session.pop("cargo", None)
    
    resp = redirect("/login")
    resp.delete_cookie('usuario')  # Remove o cookie
    return resp

# Registrando o blueprint no app
app.register_blueprint(session_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
