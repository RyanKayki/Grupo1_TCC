from flask import render_template, redirect, Blueprint, request, flash, url_for
import os
from connection.connection import conecta_database
from session.session import verifica_sessao
import mysql.connector, uuid, os

conexaoDB = conecta_database()

# Definindo o blueprint para administração
adm_blueprint = Blueprint("adm", __name__, template_folder="templates")

@adm_blueprint.route("/adm")
def adm():
    if verifica_sessao():
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute('SELECT * FROM chamado ORDER BY idChamado DESC')
            chamado = cursor.fetchall()

            cursor.execute('SELECT * FROM item')
            item = cursor.fetchall()
            item_dict = {e['idItem']: e for e in item}

            cursor.execute('SELECT * FROM local')
            local = cursor.fetchall()
            local_dict = {s['idLocal']: s for s in local}

            return render_template("adm.html", chamado=chamado, item=item_dict, local=local_dict, title="Administração", login=True)
        except Exception as e:
            print(f"Erro: {e}")
            return redirect("/error")  # redirecionar para uma página de erro
        finally:
            conexao.close()
    else:
        return redirect("/login")

@adm_blueprint.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    conn = conecta_database()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')

        try:
            if tipo == 'item':
                nome_produto = request.form['nome_produto']
                destinado_para = request.form['destinado_para']
                quantidade = request.form['quantidade']
                data_chegada = request.form['data_chegada']
                revisao_programada = request.form['revisao_programada']

                comandoSQL = f"INSERT INTO Produto (nome, destinado_para, quantidade, data_chegada, revisao_programada) VALUES ('{nome_produto}', '{destinado_para}', {quantidade}, '{data_chegada}', '{revisao_programada}')"
                cursor.execute(comandoSQL)

            elif tipo == 'funcionario':
                nome_completo = request.form['nome_completo']
                cargo = request.form['cargo']
                data_nascimento = request.form['data_nascimento']
                email = request.form['email']
                numero = request.form['numero']

                comandoSQL = f"INSERT INTO Funcionario (nome_completo, cargo, data_nascimento, email, numero) VALUES ('{nome_completo}', '{cargo}', '{data_nascimento}', '{email}', '{numero}')"
                cursor.execute(comandoSQL)

            elif tipo == 'salas':
                nome_sala = request.form['nome_sala']
                numero_sala = request.form['numero_sala']
                bloco = request.form['bloco']

                comandoSQL = f"INSERT INTO Salas (nome_sala, numero_sala, bloco) VALUES ('{nome_sala}', '{numero_sala}', '{bloco}')"
                cursor.execute(comandoSQL)

            conn.commit()
            flash('Cadastro realizado com sucesso!', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Ocorreu um erro: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
            return render_template('cadastro.html')

    # GET request: recupera os cargos
    try:
        cursor.execute("SELECT DISTINCT cargoUsuario FROM usuario")  # Substitua pelo nome correto da tabela
        cargos = cursor.fetchall()
    except Exception as e:
        cargos = []
        flash(f'Ocorreu um erro ao recuperar os cargos: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return render_template('cadastro.html', cargos=cargos)



# Rota para cadastro de chamado
@adm_blueprint.route("/cadchamados")
def cadchamados():
    login = verifica_sessao()
    if login:
        try:
            conexao = conecta_database()
            cursor = conexao.cursor(dictionary=True)

            # Obtenha as salas
            cursor.execute('SELECT * FROM local')
            salas = cursor.fetchall()

            # Obtenha os equipamentos
            cursor.execute('SELECT * FROM item')
            equipamentos = cursor.fetchall()

            title = "Cadastro de chamado"
            return render_template("cadchamados.html", title=title, login=login, salas=salas, equipamentos=equipamentos)
        except Exception as e:
            print(f"Erro: {e}")
            return redirect("/error")  # redirecionar para uma página de erro
        finally:
            conexao.close()
    else:
        return redirect("/login")



# Rota para exibir mais informações sobre um chamado
@adm_blueprint.route("/vermais/<int:idChamado>")
def sobre(idChamado):
    conexao = conecta_database()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chamado WHERE idChamado = %s", (idChamado,))
    chamado = cursor.fetchall()
    conexao.close()
    title = "Ver Mais"
    return render_template("vermais.html", title=title, chamado=chamado)


@adm_blueprint.route("/excluir/<int:idChamado>")
def excluir(idChamado):
    # Rota para excluir um chamado
    if verifica_sessao():
        conexao = conecta_database()
        cursor = conexao.cursor(dictionary=True)
        
        # Buscando a imagem associada ao chamado
        cursor.execute('SELECT img_chamado FROM chamado WHERE idChamado = %s', (idChamado,))
        chamado = cursor.fetchone()
        
        # Excluindo a imagem do chamado do diretório de imagens
        if chamado and chamado['img_chamado']:
            try:
                os.remove(os.path.join("static/img/chamado/", chamado['img_chamado']))
            except FileNotFoundError:
                pass  # Se o arquivo não for encontrado, continuamos sem falhar

        # Excluindo o chamado do banco de dados
        cursor.execute('DELETE FROM chamado WHERE idChamado = %s', (idChamado,))
        conexao.commit()
        conexao.close()
        
        return redirect('/adm')
    else:
        return redirect("/login")
