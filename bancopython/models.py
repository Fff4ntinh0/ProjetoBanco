import sqlite3
import os

caminho_diretorio = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(caminho_diretorio, "banco_site.db")

conexao = sqlite3.connect(caminho_banco)
cursor = conexao.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes_dados (
        cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento DATE NOT NULL,
        cpf_cnpj TEXT NOT NULL UNIQUE,
        endereco TEXT NOT NULL,
        telefone TEXT NOT NULL,
        email TEXT NOT NULL
    )
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS contas_bancarias (
    conta_id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_conta TEXT NOT NULL UNIQUE,
    tipo_de_conta TEXT NOT NULL,
    saldo DECIMAL(15, 2) DEFAULT 0.00,
    data_abertura DATE,
    status_da_conta TEXT NOT NULL,
    limite_credito DECIMAL(15, 2) DEFAULT 0.00,
    cliente_id INTEGER,
    agencia_id INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clientes_dados(cliente_id)
);
''')

cursor.execute('''CREATE TABLE IF NOT EXISTS historico_saldos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    valor_alterado REAL,
    saldo_atual REAL,
    data_alteracao TEXT,
    tipo_alteracao TEXT,  -- 'ganho' ou 'perda'
    FOREIGN KEY (cliente_id) REFERENCES clientes_dados(cliente_id)
);''')

cursor.execute('''CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    descricao TEXT
);''')

cursor.execute('''
CREATE TABLE compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    data_compra DATE DEFAULT (DATE('now')),
    FOREIGN KEY(cliente_id) REFERENCES clientes_dados(cliente_id),
    FOREIGN KEY(produto_id) REFERENCES produtos(id)
);''')




conexao.close()
