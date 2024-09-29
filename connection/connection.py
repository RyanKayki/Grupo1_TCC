from flask import redirect, request, jsonify, Blueprint, Flask
import mysql.connector, uuid, os

connection_blueprint = Blueprint('connection', __name__)

from session.session import verifica_sessao

# Configurações do Flask
app = Flask(__name__)
app.secret_key = "TCC"
app.config['UPLOAD_FOLDER'] = "static/uploads"  # Certifique-se de que essa pasta existe

# Função de conexão ao banco de dados
#DB CLOUD
def conecta_database():
    conexao = mysql.connector.connect(
        host='autorack.proxy.rlwy.net',  # Host do Railway
        user='root',                     # Usuário do banco de dados
        password='duRCJjOrOmbvGxbqoPDuiDzpqRreqLTD',  # Senha do banco de dados
        database='tcc',              # Nome do banco de dados fornecido pelo Railway
        port='35429'                     # Porta do banco de dados no Railway
    )
    return conexao

# Rota para cadastro de funcionário
@connection_blueprint.route("/cadastro_funcionario", methods=['POST'])
def cadastro_funcionario_json():
    if verifica_sessao():
        try:
            dados = request.json
            nome_completo = dados.get('nome_completo')
            cargo = dados.get('cargo')
            data_nascimento = dados.get('data_nascimento')
            email = dados.get('email')
            numero = dados.get('numero')

            conexao = conecta_database()
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO funcionarios (nome_completo, cargo, data_nascimento, email, numero) VALUES (%s, %s, %s, %s, %s)',
                           (nome_completo, cargo, data_nascimento, email, numero))
            conexao.commit()
            cursor.close()
            conexao.close()

            return jsonify({'message': 'Funcionário cadastrado com sucesso!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Usuário não autenticado!'}), 401

# Rota para cadastro de sala
@connection_blueprint.route('/cadastro_sala', methods=['POST'])
def cadastro_sala_json():
    if verifica_sessao():
        try:
            dados = request.json
            nome_sala = dados.get('nome_sala')
            numero_sala = dados.get('numero_sala')
            bloco = dados.get('bloco')

            conexao = conecta_database()
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO local (nome_sala, numero_sala, bloco) VALUES (%s, %s, %s)', 
                           (nome_sala, numero_sala, bloco))
            conexao.commit()
            cursor.close()
            conexao.close()

            return jsonify({'message': 'Sala cadastrada com sucesso!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Usuário não autenticado!'}), 401

# Rota para cadastro de equipamento
@connection_blueprint.route('/cadastro_equipamento', methods=['POST'])
def cadastro_equipamento_json():
    if verifica_sessao():
        try:
            dados = request.json
            nome_produto = dados.get('nome_produto')
            destinado_para = dados.get('destinado_para')
            quantidade = dados.get('quantidade')
            data_chegada = dados.get('data_chegada')
            revisao_programada = dados.get('revisao_programada')

            conexao = conecta_database()
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO item (nome_produto, destinado_para, quantidade, data_chegada, revisao_programada) VALUES (%s, %s, %s, %s, %s)', 
                           (nome_produto, destinado_para, quantidade, data_chegada, revisao_programada))
            conexao.commit()
            cursor.close()
            conexao.close()

            return jsonify({'message': 'Equipamento cadastrado com sucesso!'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Usuário não autenticado!'}), 401

# Rota para cadastro de chamado
@connection_blueprint.route("/cadastro_chamado", methods=["POST"])
def cadastro_chamado():
    if verifica_sessao():
        try:
            cargo_chamado = request.form['cargo_chamado']
            local_chamado = request.form['local_chamado']
            descricao_chamado = request.form['descricao_chamado']
            img_chamado = request.files['img_chamado']

            # Gerar um nome único para o arquivo de imagem
            id_foto = str(uuid.uuid4().hex)
            filename = id_foto + ".png"
            img_chamado.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Inserir dados na tabela
            conexao = conecta_database()
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO chamado (cargo_chamado, local_chamado, descricao_chamado, img_chamado) VALUES (%s, %s, %s, %s)', 
                           (cargo_chamado, local_chamado, descricao_chamado, filename))
            conexao.commit()
            cursor.close()
            conexao.close()

            return redirect("/adm")
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Usuário não autenticado!'}), 401

# Registrando o blueprint
app.register_blueprint(connection_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
