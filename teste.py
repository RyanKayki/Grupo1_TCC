import sqlite3

def conecta_database():
    return sqlite3.connect('database.db')


def verificar_funcionarios():
    conexao = conecta_database()
    cursor = conexao.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="funcionarios";')
    resultado = cursor.fetchone()
    if resultado:
        print("Tabela 'funcionarios' existe.")
        cursor.execute('SELECT * FROM funcionarios;')
        registros = cursor.fetchall()
        if registros:
            print("Registros na tabela 'funcionarios':")
            for registro in registros:
                print(registro)
        else:
            print("A tabela 'funcionarios' está vazia.")
    else:
        print("Tabela 'funcionarios' não existe.")
    conexao.close()

verificar_funcionarios()
