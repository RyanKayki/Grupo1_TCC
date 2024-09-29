from flask import render_template, Blueprint
from session.session import verifica_sessao

tec_blueprint = Blueprint("tec", __name__, template_folder="templates")

# Rota para a página inicial da manutenção
@tec_blueprint.route('/TecHome')
def tec_home():
    title = "Manutenção"
    login = verifica_sessao()
    return render_template("TecHome.html", title=title, login=login)
