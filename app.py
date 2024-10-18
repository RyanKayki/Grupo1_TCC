from flask import Flask
from datetime import datetime

from adm.adm import adm_blueprint
from connection.connection import connection_blueprint
from func.func import func_blueprint
from tec.tec import tec_blueprint
from session.session import session_blueprint

app = Flask(__name__)
app.secret_key = "TCC"

meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Dicionário para mapear números dos dias da semana para nomes em português
dias_da_semana = {
    0: "Seg", 1: "Ter", 2: "Qua", 
    3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"
}

@app.template_filter('data_formatada')
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
    
    # Obtém o dia da semana e o formata
    dia_semana = dias_da_semana[data_datetime.weekday()]
    
    # Formata a data manualmente usando o dicionário de meses
    dia = data_datetime.day
    mes = meses[data_datetime.month]
    ano = data_datetime.year

    return f"{dia_semana}, {dia} de {mes}"


# Registering the blueprints
app.register_blueprint(adm_blueprint)
app.register_blueprint(connection_blueprint)
app.register_blueprint(func_blueprint)
app.register_blueprint(tec_blueprint)
app.register_blueprint(session_blueprint)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
