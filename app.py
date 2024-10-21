from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "senhasecreta"

def init_db():
    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (full_name TEXT, password TEXT, email TEXT, dob TEXT, clinicas_id TEXT, FOREIGN KEY (clinicas_id) REFERENCES clinicas(id) ON DELETE SET NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS clinicas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, telefone TEXT, endereco TEXT, horario TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, FOREIGN KEY (clinicas_id) REFERENCES clinicas(id) ON DELETE SET NULL, FOREIGN KEY (users) REFERENCES users(id) ON DELETE SET NULL, date TEXT ON DELETE SET NULL)")
    c.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('clinicas', 0)")
    con.commit()
    con.close()

def add_clinicas():
    clinicas = [
        ("Posto Unicamp - Hemocentro", "0800-722-8432", "Rua Carlos Chagas, 480, Cidade Universitária, “Zeferino Vaz”", "Seg a Sáb (Inclusive em feriados): 7:30h - 15:00h"),
        ("Posto Mário Gatti - Hospital Municipal Dr. Mário Gatti", "(19) 3272-5501", "Av. Prefeito Faria Lima, 340 Pq. Itália", "Seg a Sáb (inclusive em feriados): 7:30h - 15:00h")
    ]

    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.executemany("INSERT OR IGNORE INTO clinicas (nome, telefone, endereco, horario) VALUES (?, ?, ?, ?)", clinicas)
    con.commit()
    con.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    error_password = None
    error_user = None 
    success_message = None
    error_dob = None
    full_name, email, dob = "", "", ""

    if request.method == 'POST':
        full_name = request.form['full_name']
        password = request.form['password']
        email = request.form['email']
        dob = request.form['dob']

        dob_day = int(dob[:2])
        dob_month = int(dob[3:5])
        dob_year = int(dob[6:10])

        now_date = datetime.now()
        now_year = now_date.year
        now_month = now_date.month
        now_day = now_date.day

        if (1 <= dob_day <= 31) and (1 <= dob_month <= 12) and (dob_year < now_year or (dob_year == now_year and (dob_month < now_month or (dob_month == now_month and dob_day < now_day)))):
            valid_dob = True
        else:
            valid_dob = False

        if full_name and password and email and dob:
            if valid_dob == True:
                c.execute("SELECT * FROM users WHERE full_name=? AND email=? AND password=? AND dob=?", (full_name, email, password, dob))
                if c.fetchone() is not None:
                    error_user = "Usuário já existe!"
                else:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,NULL)", (full_name, password, email, dob))
                    con.commit()
                    success_message = "Cadastro realizado com sucesso!"
                    return render_template('register.html', success_message=success_message)
            else:
                error_dob = "Data de nascimento inválida!"
                return render_template('register.html', error_dob=error_dob)
        
    con.close()
    return render_template('register.html', error_password=error_password, error_user=error_user, full_name=full_name, email=email, dob=dob)

@app.route('/login', methods=['GET', 'POST'])
def login():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    error_login = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()

        if user is None:
            error_login = "Email ou senha incorretos"
        else:
            full_name = user[0]
            session['email'] = email
            session['full_name'] = full_name
            con.close()
            return redirect(url_for('profile', full_name=full_name))  
    con.close()
    return render_template('login.html', error_login=error_login)

@app.route('/profile/<full_name>', methods=['GET', 'POST'])
def profile(full_name):
    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("SELECT * FROM users WHERE full_name=?", (full_name,))
    user_data = c.fetchone()

    if user_data is None:
        con.close()
        return "Usuário não encontrado", 404

    success_message = None  

    if request.method == 'POST':
        att_full_name = request.form['full_name']
        password = request.form['password']
        dob = request.form['dob']

        if att_full_name != user_data[0] or password != user_data[1] or dob != user_data[3]:
            c.execute("UPDATE users SET full_name=?, password=?, dob=? WHERE full_name=?", (att_full_name, password, dob, full_name))
            con.commit()
            success_message = "Dados atualizados com sucesso!"
            full_name = att_full_name 
            user_data = (att_full_name, password, user_data[2], dob)  
        else:
            success_message = "Nenhuma alteração detectada."

    con.close()
    return render_template('profile.html', full_name=user_data[0], email=user_data[2], dob=user_data[3], password=user_data[1], success_message=success_message)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    success_message = None
    error_checkbox = None
    error_clinica = None

    email = session.get('email')

    c.execute("SELECT nome, telefone, endereco, horario FROM clinicas")
    clinicas = c.fetchall()

    if request.method == 'POST':
        clinica = request.form.get('clinica')  
        check_box = 'terms' in request.form  

        if clinica:  
            if check_box:  
                c.execute("SELECT id FROM clinicas WHERE nome=?", (clinica,))
                clinica_id = c.fetchone()

                if clinica_id:
                    clinica_id = str(clinica_id[0])  

                    c.execute("SELECT clinicas_id FROM users WHERE email=?", (email,))
                    result = c.fetchone()
                    
                    if result is None or result[0] is None:
                        new_clinicas = clinica_id 
                    else:
                        indb_clinicas = result[0]
                        new_clinicas = f"{indb_clinicas},{clinica_id}"  
                    
                    c.execute("UPDATE users SET clinicas_id = ? WHERE email = ?", (new_clinicas, email))
                    con.commit()

                    success_message = "Agendamento salvo com sucesso!"
                    return render_template('agendamento.html', clinicas=clinicas, success_message=success_message)
                else:
                    error_clinica = "Clínica selecionada não existe!"
            else:
                error_checkbox = "Você precisa estar ciente dos critérios de doação!"
        else:
            error_clinica = "Você precisa escolher uma clínica!"

    return render_template('agendamento.html', clinicas=clinicas, success_message=success_message, error_checkbox=error_checkbox, error_clinica=error_clinica)

@app.route('/historic')
def historic():
    con = sqlite3.connect('users.db')
    c = con.cursor()
    message_none_clinicas = ""
    email = session.get('email')
    history = []

    c.execute("SELECT clinicas_id FROM users WHERE email=?", (email,))
    tuple_clinicas_ids = c.fetchone() #pega tupla ("1,2,1")

    if tuple_clinicas_ids and tuple_clinicas_ids[0]:
        clinicas_id_list = tuple_clinicas_ids[0].split(',') 
        clinicas_id_list = [int(clinica_id) for clinica_id in clinicas_id_list]  #[1, 2, 1]
    else:
        clinicas_id_list = []
        message_none_clinicas = "Seu histórico está vazio!"

    for clinica_id in clinicas_id_list:
        c.execute("SELECT nome FROM clinicas WHERE id=?", (clinica_id,))
        history_result = c.fetchone()
        if history_result:  
            history.append(history_result[0])

    return render_template('historic.html', history=history, date=date)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    add_clinicas()
    app.run(debug=True)

