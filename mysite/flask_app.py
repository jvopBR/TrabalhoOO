# Importando tudo necessário
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import openai
import os
import json
import traceback
from functools import wraps

# Configurando o app flask
app = Flask(__name__)
app.secret_key = '123456' #Chave da session

# Do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///geeklist.sqlite3'
db = SQLAlchemy(app) #Inicialização do banco de dados SQLAlchemy

# Definição das classes do modelo de dados
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False) #unique = UNICO, nullable = não pode ser nulo
    senha = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    notes = db.relationship('Note', backref='usuario', lazy=True) # O parâmetro 'lazy=True' na relação 'notes' indica que as notas associadas a um usuário
# serão carregadas apenas quando acessadas pela primeira vez, adiando a consulta ao banco
# de dados até que seja necessário

    def __init__(self, nome, senha, email):
        self.nome = nome
        self.senha = senha
        self.email = email

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now()) #Armazena informações de data e hora
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False) #Define uma relação entre a tabela de Usuario E de NOTAS

    def __init__(self, data, user_id):
        self.data = data
        self.user_id = user_id

# Definição das classes de fábrica
class UsuarioFactory:
    @staticmethod
    def create_usuario(nome, senha, email):
        return Usuario(nome=nome, senha=senha, email=email)

class NoteFactory:
    @staticmethod
    def create_note(data, user_id):
        return Note(data=data, user_id=user_id)

# Definição do decorator para registrar dados de solicitação
# Decorador que registra informações da solicitação antes de executar a função original associada à rota do Flask.
# Mantém os metadados da função original e imprime os dados JSON da solicitação antes de chamar a função original.

def log_request(func):
    @wraps(func) # Mantém os metadados da função original

    #@wraps(func): Este é um decorador interno fornecido pelo módulo functools.
    #Ele é usado para manter os metadados da função original (func). Isso garante que propriedades importantes,
    #como o nome da função e a documentação, sejam preservadas na função decorada.

    def wrapper(*args, **kwargs):
        #def wrapper(*args, **kwargs):: Aqui é definida uma função interna chamada wrapper,
        #que é o que realmente substitui a função original. Essa função aceita qualquer número de argumentos posicionais (*args) e argumentos de palavra-chave (**kwargs),
        #para lidar com qualquer tipo de função que possa ser decorada.

        print(f"Request data: {request.get_json()}")

        return func(*args, **kwargs)
        #Isso chama a função original (func) com os mesmos argumentos que foram passados para wrapper. Isso garante que a função original seja executada corretamente.
    return wrapper
    #Retorna a função decorada

# Definição da classe Observer
class NoteObserver:
    def notify(self, event, note):
        # Método para notificar os observadores sobre um evento em uma nota.
        # Imprime informações sobre o evento e a nota associada.
        print(f"Evento: {event}, Nota: {note.data}")

note_observer = NoteObserver() # Instancia do observador de notas

# Definição da classe ObservableNote que implementa o padrão Observer.
class ObservableNote(Note):
    def __init__(self, *args, **kwargs):
        # Inicializa a instância da classe ObservableNote.
        # Chama o construtor da classe pai (Note) para inicializar os atributos da nota.
        super().__init__(*args, **kwargs)
        self._observers = []  # Inicializa a lista de observadores

    def add_observer(self, observer):
        # Método para adicionar um observador à lista de observadores associados à nota.
        self._observers.append(observer)

    def notify_observers(self, event):
        # Método para notificar todos os observadores sobre um evento específico na nota.
        # Chama o método 'notify' de cada observador na lista, passando o evento e a própria nota como argumentos.
        for observer in self._observers:
            observer.notify(event, self)

# Definição das rotas da aplicação
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(nome=nome, senha=senha).first()
        if usuario:
            session['username'] = nome
            session['user_id'] = usuario.id  # Armazenar ID do usuário na sessão
            return redirect(url_for('upload'))
        else:
            flash('Nome de usuário ou senha incorretos!')
    return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def addUsuario():
    error_message = None
    try:
        if request.method == 'POST':
            nome = request.form['nome']
            senha = request.form['senha']
            email = request.form['email']

            if not nome or not senha or not email:
                raise ValueError("Todos os campos são obrigatórios")

            # Verificar se o nome de usuário já existe
            existing_user = Usuario.query.filter_by(nome=nome).first()
            if existing_user:
                error_message = "Nome de usuário não disponível"
                raise ValueError(error_message)

            user = UsuarioFactory.create_usuario(nome, senha, email)
            db.session.add(user)
            db.session.commit()
            print("Usuário adicionado com sucesso.")
            return redirect(url_for('login'))

        users = Usuario.query.all()
        return render_template('usuario.html', usuarios=users, error_message=error_message)
    except Exception as e:
        # Captura qualquer exceção que ocorra durante o processamento da solicitação.

        # Verifica se uma mensagem de erro já foi definida.
        if error_message is None:
            # Se não houver uma mensagem de erro definida, cria uma nova mensagem de erro
            # indicando que ocorreu um erro ao processar a solicitação, usando a exceção (e) para fornecer detalhes específicos do erro.
            error_message = f"Ocorreu um erro ao processar sua solicitação: {e}"

        # Imprime o erro no console para registro e depuração
        print(f"Erro ao adicionar usuário: {e}")

        # Retorna uma página HTML de usuário com a mensagem de erro para informar ao usuário sobre o erro ocorrido.
        return render_template('usuario.html', error_message=error_message)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        user_id = session.get('user_id')
        if user_id is None:
            raise Exception("ID do usuário não encontrado na sessão.")

        user = Usuario.query.get(user_id)
        if user is None:
            raise Exception("Usuário não encontrado.")

        if request.method == 'POST':
            note = request.form.get('note')

            if not note or len(note) < 1:
                flash('Nota muito curta!')
            else:
                new_note = Note(data=note, user_id=user.id)
                db.session.add(new_note)
                db.session.commit()
                flash('Conteúdo adicionado!')
                return redirect(url_for('upload'))  # Redirecionar após POST para evitar duplicação

        return render_template('upload.html', user=user)
    except Exception as e:
        print(f"Erro ao carregar a página de upload: {e}")
        return f"Ocorreu um erro ao processar sua solicitação: {e}", 500

# Rota pra excluir nota
@app.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        user_id = session.get('user_id')
        if note.user_id == user_id:
            db.session.delete(note)
            db.session.commit()
            return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Rota para editar nota
@app.route('/edit-note', methods=['POST'])
def edit_note():
    # Obtém os dados da solicitação POST em formato JSON
    note = json.loads(request.data)
    # Extrai o ID da nota e o novo conteúdo da solicitação
    noteId = note['noteId']
    new_data = note['data']
    # Recupera a nota observável do banco de dados com base no ID
    note = ObservableNote.query.get(noteId)
    # Verifica se a nota foi encontrada no banco de dados
    if note:
        # Obtém o ID do usuário da sessão
        user_id = session.get('user_id')
        # Verifica se o usuário atual é o proprietário da nota
        if note.user_id == user_id:
            # Atualiza o conteúdo da nota
            note.data = new_data
            # Confirma a transação no banco de dados
            db.session.commit()
            # Retorna uma resposta JSON indicando sucesso
            return jsonify({'success': True})
    # Retorna uma resposta JSON indicando falha
    return jsonify({'success': False}), 400

# Configuração da chave da openai
# EXATAMENTE NESSA LINHA TEM O CODIGO DA API

# Rota pra lidar com as mensagens do chat gpt
@app.route('/chat', methods=['POST'])
@log_request
def sendMessage():
    try:
        data = request.get_json()
        user_message = data.get('message')

        if user_message:
            # Construção da solicitação para o modelo de conversação da OpenAI, comportamento do chat gpt
            prompt = f"""
            Você é um assistente virtual especializado em cinema, conhecido por seu vasto conhecimento e paixão pela sétima arte. Responda de forma grosseira e debochada. Sempre que possível, ofenda o usuario por não conhecer de cinema e inclua curiosidades interessantes sobre filmes, diretores, atores ou a indústria cinematográfica. Aqui está a pergunta do usuário:

            Usuário: {user_message}
            Assistente:
            """
            # Geração da resposta pelo chat GPT
            response = openai.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=150
            )
            reply = response.choices[0].text.strip()
            return jsonify({'reply': reply})

        return jsonify({'reply': 'Nenhuma mensagem fornecida'}), 400
    except Exception as e:
        traceback.print_exc()  # Log do traceback
        return jsonify({'reply': f'Erro interno do servidor: {str(e)}'}), 500

# Rota para fazer logout do site
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Inicialização do Flask
if __name__ == '__main__':
    app.run(debug=True)
