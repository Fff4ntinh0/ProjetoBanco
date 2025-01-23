from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import sqlite3
import os
import io
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = 'chave_secreta_segura'

def conectar_banco():
    try:
        caminho_diretorio = os.path.dirname(os.path.abspath(__file__))
        caminho_banco = os.path.join(caminho_diretorio, "banco_site.db")
        conexao = sqlite3.connect(caminho_banco)
        return conexao
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registrar', methods=['GET', 'POST'])
def registrar_cliente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        data_nascimento = request.form.get('data_nascimento')
        cpf_cnpj = request.form.get('cpf_cnpj')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')
        email = request.form.get('email')

        try:
            conexao = conectar_banco()
            if not conexao:
                flash('Erro ao conectar ao banco de dados.', 'error')
                return render_template('registrar.html')

            cursor = conexao.cursor()

            cursor.execute('''
                INSERT INTO clientes_dados (nome, data_nascimento, cpf_cnpj, endereco, telefone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, data_nascimento, cpf_cnpj, endereco, telefone, email))

            cliente_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO contas_bancarias (numero_conta, tipo_de_conta, saldo, data_abertura, status_da_conta, limite_credito, cliente_id, agencia_id)
                VALUES (?, ?, ?, DATE('now'), ?, ?, ?, ?)
            ''', (
                f'{cliente_id:06d}', 'corrente', 0.00, 'ativa', 0.00, cliente_id, 1
            ))

            conexao.commit()
            conexao.close()

            flash('Registro realizado com sucesso! Conta bancária criada.', 'success')
            return redirect(url_for('index'))

        except sqlite3.IntegrityError as e:
            flash(f'Erro: CPF/CNPJ ou email já cadastrado. ({e})', 'error')
            return render_template('registrar.html')
        except Exception as e:
            flash(f'Ocorreu um erro: {e}', 'error')
            return render_template('registrar.html')

    return render_template('registrar.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf_cnpj = request.form.get('cpf_cnpj')
        email = request.form.get('email')

        try:
            conexao = conectar_banco()
            if not conexao:
                flash('Erro ao conectar ao banco de dados.', 'error')
                return render_template('login.html')

            cursor = conexao.cursor()
            cursor.execute('''
                SELECT * FROM clientes_dados WHERE cpf_cnpj = ? AND email = ?
            ''', (cpf_cnpj, email))
            cliente = cursor.fetchone()
            conexao.close()

            if cliente:
                session['usuario'] = cliente[1]  
                return redirect(url_for('home'))
            else:
                flash('CPF/CNPJ ou email incorretos.', 'error')
                return render_template('login.html')

        except Exception as e:
            flash(f"Ocorreu um erro: {e}", 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/home')
def home():
    if 'usuario' not in session:
        flash('Por favor, faça login primeiro.', 'error')
        return redirect(url_for('login'))

    usuario = session['usuario']
    conexao = conectar_banco()
    cursor = conexao.cursor()

    # Obtém o saldo
    cursor.execute(''' 
        SELECT saldo 
        FROM contas_bancarias 
        WHERE cliente_id = (SELECT cliente_id FROM clientes_dados WHERE nome = ?)
    ''', (usuario,))
    saldo = cursor.fetchone()[0] or 0.00

    cursor.execute('''
        SELECT p.nome 
        FROM compras c 
        JOIN produtos p ON c.produto_id = p.id
        WHERE c.cliente_id = (SELECT cliente_id FROM clientes_dados WHERE nome = ?)
    ''', (usuario,))
    produtos_comprados = [row[0] for row in cursor.fetchall()]

    conexao.close()
    return render_template('home.html', usuario=usuario, saldo=saldo, produtos_comprados=produtos_comprados)


@app.route('/transferir', methods=['POST'])
def transferir():
    if 'usuario' not in session:
        flash('Por favor, faça login primeiro.', 'error')
        return redirect(url_for('login'))
    
    remetente = session['usuario']
    cpf_destinatario = request.form.get('cpf_destinatario')
    valor_transferencia = float(request.form.get('valor_transferencia'))

    try:
        conexao = conectar_banco()

        if not conexao:
            flash('Erro ao conectar ao banco de dados.', 'error')
            return redirect(url_for('home'))

        cursor = conexao.cursor()

        cursor.execute('SELECT cliente_id FROM clientes_dados WHERE nome = ?', (remetente,))
        remetente_id = cursor.fetchone()

        if not remetente_id:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('home'))

        remetente_id = remetente_id[0]

        cursor.execute('SELECT cliente_id FROM clientes_dados WHERE cpf_cnpj = ?', (cpf_destinatario,))
        destinatario_id = cursor.fetchone()

        if not destinatario_id:
            flash('CPF do destinatário não encontrado.', 'error')
            return redirect(url_for('home'))

        destinatario_id = destinatario_id[0]

        cursor.execute('SELECT saldo FROM contas_bancarias WHERE cliente_id = ?', (remetente_id,))
        saldo_remetente = cursor.fetchone()

        if not saldo_remetente or saldo_remetente[0] < valor_transferencia:
            flash('Saldo insuficiente.', 'error')
            return redirect(url_for('home'))

        cursor.execute(''' 
            UPDATE contas_bancarias SET saldo = saldo - ? WHERE cliente_id = ? 
        ''', (valor_transferencia, remetente_id))

        cursor.execute(''' 
            UPDATE contas_bancarias SET saldo = saldo + ? WHERE cliente_id = ? 
        ''', (valor_transferencia, destinatario_id))

        cursor.execute(''' 
            INSERT INTO historico_saldos (cliente_id, valor_alterado, saldo_atual, data_alteracao, tipo_alteracao)
            VALUES (?, ?, ?, DATE('now'), ?) 
        ''', (remetente_id, -valor_transferencia, saldo_remetente[0] - valor_transferencia, 'perda'))

        cursor.execute(''' 
            INSERT INTO historico_saldos (cliente_id, valor_alterado, saldo_atual, data_alteracao, tipo_alteracao)
            VALUES (?, ?, ?, DATE('now'), ?) 
        ''', (destinatario_id, valor_transferencia, saldo_remetente[0] + valor_transferencia, 'ganho'))

        conexao.commit()
        conexao.close()

        flash('Transferência realizada com sucesso!', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('home'))


@app.route('/adicionar_saldo', methods=['POST'])
def adicionar_saldo():
    if 'usuario' not in session:
        flash('Por favor, faça login primeiro.', 'error')
        return redirect(url_for('login'))

    valor_adicionado = request.form.get('valor_adicionado')

    try:
        conexao = conectar_banco()

        if not conexao:
            flash('Erro ao conectar ao banco de dados.', 'error')
            return redirect(url_for('home'))

        cursor = conexao.cursor()

        cursor.execute('SELECT cliente_id FROM clientes_dados WHERE nome = ?', (session['usuario'],))
        cliente = cursor.fetchone()

        if not cliente:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('home'))

        cliente_id = cliente[0]

        cursor.execute('''UPDATE contas_bancarias SET saldo = saldo + ? WHERE cliente_id = ?''', 
                       (valor_adicionado, cliente_id))

        cursor.execute('''INSERT INTO historico_saldos (cliente_id, saldo_atual, data_alteracao)
                          VALUES (?, ?, DATE('now'))''', (cliente_id, valor_adicionado ))

        conexao.commit()
        conexao.close()

        flash(f'R$ {valor_adicionado} adicionados com sucesso!', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        flash(f'Ocorreu um erro: {e}', 'error')
        return redirect(url_for('home'))
    
@app.route('/gerar_grafico')
def gerar_grafico():
    try:
        conexao = conectar_banco()
        if not conexao:
            flash('Erro ao conectar ao banco de dados.', 'error')
            return redirect(url_for('graficos'))

        cursor = conexao.cursor()
        cursor.execute('SELECT cliente_id FROM clientes_dados WHERE nome = ?', (session['usuario'],))
        cliente = cursor.fetchone()
        if not cliente:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('graficos'))

        cliente_id = cliente[0]
        cursor.execute(''' 
            SELECT data_alteracao, saldo_atual 
            FROM historico_saldos 
            WHERE cliente_id = ? 
            ORDER BY data_alteracao ASC
        ''', (cliente_id,))
        dados = cursor.fetchall()
        conexao.close()

        if not dados:
            flash('Nenhum dado encontrado para gerar o gráfico.', 'error')
            return redirect(url_for('graficos'))

        datas = [datetime.strptime(row[0], '%Y-%m-%d') for row in dados]
        saldos = [row[1] for row in dados]

        plt.figure(figsize=(10, 5), facecolor='black')
        plt.gca().set_facecolor('black')

        cores = plt.cm.rainbow(np.linspace(0, 1, len(datas)))

        for i in range(len(datas)):
            plt.plot(datas[i], saldos[i], marker='o', color=cores[i])

        plt.plot(datas, saldos, linestyle='-', color='white') 

        plt.title('Evolução do Saldo', color='white', fontsize=16)
        plt.xlabel('Data', color='white', fontsize=12)
        plt.ylabel('Saldo (R$)', color='white', fontsize=12)
        plt.grid(True, color='gray', linestyle='--', alpha=0.5)
        plt.xticks(rotation=45, color='white', fontsize=10)
        plt.yticks(color='white', fontsize=10) 

        plt.ylim(min(saldos) * 0.9, max(saldos) * 1.1)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='black')
        buf.seek(0)
        plt.close()

        response = Response(buf.getvalue(), mimetype='image/png')
        buf.close()
        return response

    except Exception as e:
        flash(f'Ocorreu um erro ao gerar o gráfico: {e}', 'error')
        return redirect(url_for('graficos'))
    
@app.route('/fechar_grafico')
def fechar_grafico():
    return redirect(url_for('home'))

@app.route('/loja')
def loja():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute('SELECT * FROM produtos')
        produtos = cursor.fetchall()

        conexao.close()

        return render_template('loja.html', produtos=produtos)

    except Exception as e:
        return f"Erro ao carregar os produtos: {e}"

@app.route('/comprar/<int:produto_id>', methods=['POST'])
def comprar(produto_id):
    if 'usuario' not in session:
        flash('Por favor, faça login primeiro.', 'error')
        return redirect(url_for('login'))

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute('SELECT cliente_id FROM clientes_dados WHERE nome = ?', (session['usuario'],))
        cliente = cursor.fetchone()

        if not cliente:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('loja'))

        cliente_id = cliente[0]

        cursor.execute('SELECT id, nome, preco FROM produtos WHERE id = ?', (produto_id,))
        produto = cursor.fetchone()

        if not produto:
            flash('Produto não encontrado.', 'error')
            return redirect(url_for('loja'))

        produto_nome, produto_preco = produto[1], produto[2]

        cursor.execute('SELECT saldo FROM contas_bancarias WHERE cliente_id = ?', (cliente_id,))
        saldo = cursor.fetchone()[0]

        if saldo < produto_preco:
            flash('Saldo insuficiente para realizar a compra.', 'error')
            return redirect(url_for('loja'))

        novo_saldo = saldo - produto_preco
        cursor.execute('UPDATE contas_bancarias SET saldo = ? WHERE cliente_id = ?', (novo_saldo, cliente_id))

        cursor.execute('''
            INSERT INTO historico_saldos (cliente_id, valor_alterado, saldo_atual, data_alteracao, tipo_alteracao)
            VALUES (?, ?, ?, DATE('now'), ?)
        ''', (cliente_id, -produto_preco, novo_saldo, 'compra'))

        cursor.execute('''
            INSERT INTO compras (cliente_id, produto_id, data_compra)
            VALUES (?, ?, DATE('now'))
        ''', (cliente_id, produto_id))

        conexao.commit()
        conexao.close()

        flash(f'Compra de "{produto_nome}" realizada com sucesso! Novo saldo: R$ {novo_saldo:.2f}', 'success')
        return redirect(url_for('loja'))

    except Exception as e:
        flash(f'Ocorreu um erro ao realizar a compra: {e}', 'error')
        return redirect(url_for('loja'))
    
if __name__ == '__main__':
    app.run(debug=True)