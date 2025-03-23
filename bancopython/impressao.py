import sqlite3
import os

caminho_diretorio = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(caminho_diretorio, "banco_site.db")

conexao = sqlite3.connect(caminho_banco)
cursor = conexao.cursor()

# Função para imprimir os dados de uma tabela
def imprimir_dados_tabela(nome_tabela):
    try:
        # Garante que o banco seja criado no mesmo diretório do script
        caminho_diretorio = os.path.dirname(os.path.abspath(__file__))
        caminho_banco = os.path.join(caminho_diretorio, "banco_site.db")

        conexao = sqlite3.connect(caminho_banco)
        cursor = conexao.cursor()

        # Recuperar dados da tabela
        cursor.execute(f"SELECT * FROM {nome_tabela}")
        colunas = [descricao[0] for descricao in cursor.description]
        dados = cursor.fetchall()

        # Exibir os dados no console
        print(f"\nDados da tabela '{nome_tabela}':")
        print(" | ".join(colunas))  # Cabeçalho das colunas
        print("-" * 50)
        for linha in dados:
            print(" | ".join(map(str, linha)))


        conexao.close()
    except sqlite3.Error as erro:
        print(f"Erro ao acessar a tabela {nome_tabela}: {erro}")

# Chamando a função para as tabelas
imprimir_dados_tabela("clientes_dados")
imprimir_dados_tabela("contas_bancarias")

cursor.execute('''
    INSERT INTO produtos (nome, preco, descricao) VALUES
    ('Notebook Gamer', 5000.00, 'Notebook de alta performance para jogos.'),
    ('Fone de Ouvido Bluetooth', 250.00, 'Fone com tecnologia Bluetooth e som de alta qualidade.'),
    ('Teclado Mecânico RGB', 400.00, 'Teclado mecânico com iluminação RGB.'),
    ('Mouse Gamer', 200.00, 'Mouse ergonômico e preciso para jogos.'),
    ('Monitor UltraWide 34"', 3000.00, 'Monitor UltraWide de 34 polegadas para maior imersão.'),
    ('Cadeira Gamer', 1500.00, 'Cadeira ergonômica para longas horas de uso.'),
    ('Smartphone Top de Linha', 4000.00, 'Smartphone com as melhores especificações do mercado.'),
    ('Console de Videogame', 4500.00, 'Console de última geração para diversão garantida.'),
    ('SSD 1TB NVMe', 600.00, 'SSD de alta velocidade com capacidade de 1TB.'),
    ('Headset com Microfone', 300.00, 'Headset com microfone integrado para comunicação clara.');
''')


# Confirma as alterações
conexao.commit()
conexao.close()
imprimir_dados_tabela("produtos")