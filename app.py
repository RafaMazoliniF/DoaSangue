from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "senhasecreta"

def init_db():
    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, password TEXT, email TEXT, dob TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clinicas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, telefone TEXT, endereco TEXT, horario TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS agendamentos (users_id INTEGER, clinicas_id INTEGER, date TEXT, observacao TEXT, FOREIGN KEY (clinicas_id) REFERENCES clinicas(id) ON DELETE SET NULL, FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE SET NULL)")
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
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (None, full_name, password, email, dob))
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
            session['email'] = email
            session['full_name'] = user[1]
            session['user_id'] = user[0]  
            con.close()
            return redirect(url_for('profile', user_id=user[0]))  
    con.close()
    return render_template('login.html', error_login=error_login)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')  
    if not user_id:
        return redirect(url_for('login'))  

    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user_data = c.fetchone()

    if user_data is None:
        con.close()
        return "Usuário não encontrado", 404

    success_message = None

    if request.method == 'POST':
        att_full_name = request.form['full_name']
        password = request.form['password']
        dob = request.form['dob']

        if att_full_name != user_data[1] or password != user_data[2] or dob != user_data[3]:
            c.execute("UPDATE users SET full_name=?, password=?, dob=? WHERE id=?", (att_full_name, password, dob, user_id))
            con.commit()
            success_message = "Dados atualizados com sucesso!"
            user_data = (user_id, att_full_name, password, user_data[3], dob)
        else:
            success_message = "Nenhuma alteração detectada."

    con.close()
    return render_template('profile.html', full_name=user_data[1], email=user_data[3], dob=user_data[4], password=user_data[2], success_message=success_message)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    success_message = None
    error_checkbox = None
    error_clinica = None
    error_date = None

    email = session.get('email')

    c.execute("SELECT nome, telefone, endereco, horario FROM clinicas")
    clinicas = c.fetchall()

    if request.method == 'POST':
        clinica = request.form.get('clinica')  
        check_box = 'terms' in request.form
        date_str = request.form.get('data')  
        observation = request.form.get('observacao')  

        if clinica and date_str:
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d')
                today = datetime.today()

                if booking_date.date() <= today.date():
                    error_date = "A data do agendamento deve ser no futuro."
                else:
                    if check_box:
                        c.execute("SELECT id FROM clinicas WHERE nome=?", (clinica,))
                        clinica_id = c.fetchone()

                        if clinica_id:
                            clinica_id = clinica_id[0]

                            c.execute("SELECT id FROM users WHERE email=?", (email,))
                            result = c.fetchone()
                            result_id = result[0]

                            c.execute("INSERT INTO agendamentos (users_id, clinicas_id, date, observacao) VALUES (?, ?, ?, ?)", 
                                (result_id, clinica_id, date_str, observation))
                            con.commit()

                            success_message = "Agendamento salvo com sucesso!"
                            return render_template('agendamento.html', clinicas=clinicas, success_message=success_message)
                        else:
                            error_clinica = "Clínica selecionada não existe!"
                    else:
                        error_checkbox = "Você precisa estar ciente dos critérios de doação!"
            except ValueError:
                error_date = "Formato de data inválido. Use o formato AAAA-MM-DD."
        else:
            error_clinica = "Você precisa escolher uma clínica e fornecer uma data!"

    return render_template('agendamento.html', clinicas=clinicas, success_message=success_message, error_checkbox=error_checkbox, error_clinica=error_clinica, error_date=error_date)

@app.route('/historic')
def historic():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    email = session.get('email')
    history = []

    c.execute("SELECT id FROM users WHERE email=?", (email,))
    user_id = c.fetchone()

    if user_id:
        user_id = user_id[0]
        
        c.execute("SELECT clinicas.nome, agendamentos.date, agendamentos.observacao, agendamentos.rowid FROM agendamentos JOIN clinicas ON agendamentos.clinicas_id = clinicas.id WHERE agendamentos.users_id = ?", (user_id,))
        history = [(nome, datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y'), observacao, rowid) for nome, date, observacao, rowid in c.fetchall()]

    con.close()
    
    if not history:
        message_none_clinicas = "Seu histórico está vazio!"
    else:
        message_none_clinicas = None

    return render_template('historic.html', history=history, message_none_clinicas=message_none_clinicas)

@app.route('/add_donation', methods=['GET', 'POST'])
def add_donation():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    email = session.get('email')

    c.execute("SELECT nome FROM clinicas")
    clinicas = c.fetchall()

    success_message = None
    error_date = None

    if request.method == 'POST':
        clinica = request.form.get('clinica')
        date_str = request.form.get('data')
        observation = request.form.get('observacao')

        if clinica and date_str:
            try:
                booking_date = datetime.strptime(date_str, '%Y-%m-%d')
                today = datetime.today()

                if booking_date.date() > today.date():
                    error_date = "A data da doação deve ser no passado."
                else:
                    c.execute("SELECT id FROM clinicas WHERE nome=?", (clinica,))
                    clinica_id = c.fetchone()

                    if clinica_id:
                        clinica_id = clinica_id[0]

                        c.execute("SELECT id FROM users WHERE email=?", (email,))
                        user_id = c.fetchone()[0]

                        c.execute("INSERT INTO agendamentos (users_id, clinicas_id, date, observacao) VALUES (?, ?, ?, ?)", 
                                  (user_id, clinica_id, date_str, observation))
                        con.commit()

                        success_message = "Doação adicionada com sucesso!"
                    else:
                        error_clinica = "Clínica selecionada não existe!"
            except ValueError:
                error_date = "Formato de data inválido. Use o formato AAAA-MM-DD."

    con.close()
    return render_template('add_donation.html', clinicas=clinicas, success_message=success_message, error_date=error_date)

@app.route('/edit_donation/<int:donation_id>', methods=['GET', 'POST'])
def edit_donation(donation_id):
    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("SELECT nome FROM clinicas")
    clinicas = c.fetchall()

    c.execute("SELECT clinicas.nome, agendamentos.date, agendamentos.observacao FROM agendamentos JOIN clinicas ON agendamentos.clinicas_id = clinicas.id WHERE agendamentos.rowid = ?", (donation_id,))
    donation = c.fetchone()

    if request.method == 'POST':
        clinica = request.form.get('clinica')
        date_str = request.form.get('data')
        observation = request.form.get('observacao')

        c.execute("SELECT id FROM clinicas WHERE nome=?", (clinica,))
        clinica_id = c.fetchone()[0]

        c.execute("UPDATE agendamentos SET clinicas_id = ?, date = ?, observacao = ? WHERE rowid = ?", 
                  (clinica_id, date_str, observation, donation_id))
        con.commit()
        con.close()

        return redirect(url_for('historic'))

    con.close()
    return render_template('edit_donation.html', donation=donation, clinicas=clinicas)

@app.route('/delete_donation/<int:donation_id>')
def delete_donation(donation_id):
    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("DELETE FROM agendamentos WHERE rowid = ?", (donation_id,))
    con.commit()
    con.close()

    return redirect(url_for('historic'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    add_clinicas()
    app.run(debug=True)

