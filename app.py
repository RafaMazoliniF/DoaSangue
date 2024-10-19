from flask import Flask, render_template, request, redirect, url_for
import sqlite3, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "senhasecreta"

def init_db():
    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (full_name TEXT, password TEXT, email TEXT, dob TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clinicas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, telefone TEXT, endereco TEXT, horario TEXT)")
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

        if (dob_year < now_year - 18) or (dob_year == now_year - 18 and (dob_month < now_month or (dob_month == now_month and dob_day <= now_day))):
            valid_dob = True
        else:
            valid_dob = False

        if full_name and password and email and dob:
            if valid_dob == True:
                c.execute("SELECT * FROM users WHERE full_name=? AND email=? AND password=? AND dob=?", (full_name, email, password, dob))
                if c.fetchone() is not None:
                    error_user = "Usuário já existe!"
                else:
                    c.execute("INSERT INTO users VALUES (?,?,?,?)", (full_name, password, email, dob))
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

    if request.method == 'POST':
        clinica = request.form.get('clinica')
        email = request.form['email']

        if clinica:
            c.execute("ALTER TABLE users")
            c.execute("ADD clinicas_id INT") 

            id_clinica = c.execute("SELECT id FROM clinicas WHERE nome=? ", (clinica,))

            if clinica: #n tem valor
                c.execute("UPDATE users SET clinicas_id = CONCAT(clinicas_id, ', ?')", (id_clinica,))
                success_message = "Agendamento salvo com sucesso!"
                
            return render_template('agendamento.html', success_message=success_message)

    return render_template('agendamento.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    add_clinicas()
    app.run(debug=True)
