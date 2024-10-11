from flask import render_template, Blueprint
from session.session import verifica_sessao

func_blueprint = Blueprint("func", __name__, template_folder="templates")

# Rota para a página inicial dos funcionários
@func_blueprint.route('/FuncHome')
def func_home():
    title = "Funcionários"
    login = verifica_sessao()
    return render_template("FuncHome.html", title=title, login=login)

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
