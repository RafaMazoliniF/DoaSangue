from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, get_flashed_messages
import sqlite3, requests, re, smtplib
from datetime import datetime
from geopy.geocoders import Nominatim
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "senhasecreta"

#no profile, ao alterar a senha, não está verificando se as senhas estão iguais
def get_cep(endereco):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={endereco}"
    resp = requests.get(url)
    
    if resp.status_code == 200:
        data = resp.json()
        if data:
            lat, lon = data[0]['lat'], data[0]['lon']
            via_cep_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            via_cep_response = requests.get(via_cep_url)
            
            if via_cep_response.status_code == 200:
                via_cep_data = via_cep_response.json()
                return via_cep_data['address'].get('postcode')
            
    return None

def verify_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    return bool(re.match(regex, email))

def init_db():
    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, password TEXT, email TEXT, dob TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clinicas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, telefone TEXT, endereco TEXT, horario TEXT, cep TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS agendamentos (users_id INTEGER, clinicas_id INTEGER, date TEXT, observacao TEXT, FOREIGN KEY (clinicas_id) REFERENCES clinicas(id) ON DELETE SET NULL, FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE SET NULL)")
    c.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('clinicas', 0)")
    con.commit()
    con.close()

def add_clinicas():
    clinicas = [
        ("Posto Unicamp - Hemocentro", "0800-722-8432", "Rua Carlos Chagas, 480 - Cidade Universitária", "Seg a Sáb (Inclusive em feriados): 7:30h - 15:00h", ""),
        ("Posto Mário Gatti - Hospital Municipal Dr. Mário Gatti", "(19) 3272-5501", "Av. Prefeito Faria Lima, 340 - Pq. Itália", "Seg a Sáb (inclusive em feriados): 7:30h - 15:00h", ""),
        ("Centro de Hemoterapia Celular em Medicina de Campinas", "(19) 3734-3193", "Rua Onze de Agosto, 415 - Centro", "Seg a Sex: 7:30h - 12:30h / Sáb: 8:00h - 12:00h", ""),
        ("Hemocamp Clínica de Hemoterapia", "(19) 3235-2259", "Rua Irmã Serafina, 259 - Centro", "Seg a Sex: 8:00h as 11:00h", ""),
        ("Posto de Coleta Boldrini", "(19) 3887-5028", "Av. Dr. Gabriel Porto, 1270 - Cidade Universitária", "Seg a Sex: 8:00h as 12:00h", "")
    ]

    con = sqlite3.connect('users.db')
    c = con.cursor()
    c.executemany("INSERT OR IGNORE INTO clinicas (nome, telefone, endereco, horario, cep) VALUES (?, ?, ?, ?, ?)", clinicas)

    c.execute("SELECT endereco FROM clinicas")
    endereco = c.fetchall()
    
    for end in endereco:
        end_format = re.match(r'^(.*?)(,)', end[0])
        end_final = end_format.group(1).strip() + " - Campinas"

        cep = get_cep(end_final)

        if cep:  
            c.execute("UPDATE clinicas SET cep=? WHERE endereco=?", (cep, end[0]))
    
    con.commit()
    con.close()

@app.route('/send_email', methods=['POST'])
def send_email():
    smtp_server = "smtp.gmail.com"
    port = 587  
    sender = "solidaria.gota@gmail.com"
    password = "hybd wqnw piyj ptzr"

    data = request.get_json()
    receiver = data.get("email")
    full_name = data.get("full_name")   
    #date = get_date()

    if not receiver:
        return jsonify({"error": "Email destinatário é necessário"}), 400

    message = MIMEMultipart()
    message["Subject"] = "A ESPERA ACABOU!! 🎉"
    message["From"] = sender
    message["To"] = receiver

    html = f""" 
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px;">
            <table align="center" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #ddd;">
                <tr>
                    <td style="padding: 20px; text-align: center; background-color: #ff0000; color: white; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                        <h1 style="margin: 0; font-size: 28px;">Gota Solidária</h1>
                        <p style="margin: 5px 0; font-size: 18px;">Sua ajuda é essencial, e estamos felizes em contar com você!</p>
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 20px;">
                        <p style="font-size: 18px;">Olá <strong>{full_name}</strong>,</p>
                        <p style="font-size: 18px;">Os 3 meses mínimos de intervalo já acabaram, e você está apto para doar novamente!</p>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="http://127.0.0.1:5000/booking" style="display: inline-block; padding: 12px 30px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">Agende sua consulta agora</a>
                        </p>
                        
                        <p style="font-size: 18px;">Estamos ansiosos para vê-lo novamente e agradecemos seu compromisso em salvar vidas.</p>
                        
                        <p style="font-size: 16px; color: #555; text-align: center; margin-top: 20px;">
                            Atenciosamente,<br>Equipe Gota Solidária
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    
    try:
        with smtplib.SMTP(smtp_server, port) as s:
            s.starttls()
            s.login(sender, password)
            s.sendmail(sender, receiver, message.as_string())
        return jsonify({"message": "Email enviado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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
        conf_password = request.form['conf_password']

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

        if password == conf_password:
            valid_password = True
        else:
            valid_password = False

        if full_name and password and email and dob:
            if valid_dob == True:
                if valid_password == True:
                    c.execute("SELECT * FROM users WHERE email=? ", (email, ))
                    if c.fetchone() is not None:
                        error_user = "Usuário já existe!"
                    else:
                        c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (None, full_name, password, email, dob))
                        con.commit()
                        success_message = "Cadastro realizado com sucesso!"
                        return render_template('register.html', success_message=success_message)
                else:
                    error_password = "Senhas precisam ser iguais!"
                    return render_template('register.html', error_password=error_password)
            else:
                error_dob = "Data de nascimento inválida!"
                return render_template('register.html', error_dob=error_dob)
        
    con.close()
    return render_template('register.html', error_password=error_password, error_user=error_user, full_name=full_name, email=email, dob=dob)

#fazer verificação se a senha/ usuario estao certo ou se nem existe o usuario - DONE
@app.route('/login', methods=['GET', 'POST'])
def login():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    error_login, error_cred = None, None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user_data = c.fetchone()

        if user_data is None:
            error_login = "Usuário não cadastrado! Crie sua conta agora."
        else:
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            valid_user = c.fetchone()

            if valid_user is None:
                error_cred = "Senha incorreta!"
            else:
                session['email'] = email
                session['full_name'] = valid_user[1]
                session['user_id'] = valid_user[0]
                con.close()
                return redirect(url_for('profile', user_id=valid_user[0]))  
    con.close()
    return render_template('login.html', error_login=error_login, error_cred=error_cred)

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

@app.route('/clinicas_proximas')
def clinicas_proximas():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("SELECT cep FROM clinicas")
    cep_result = c.fetchall()

    lista_cep = [cep[0] for cep in cep_result]

    con.commit()
    con.close()

    return render_template('clinicas_proximas.html', lista_cep=lista_cep)

@app.route('/get_clinics', methods=['GET'])
def get_clinics():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    c.execute("SELECT nome, endereco, cep FROM clinicas")
    clinics = c.fetchall()
    con.close()

    clinics_list = [{'nome': nome, 'endereco': endereco, 'cep': cep} for nome, endereco, cep in clinics]
    return jsonify(clinics_list)

#precisa arrumar o forgot e recovery (mensagens de erro e sucesso n aparecem)
#email em recovery_password não ta sendo passado como parametro corretamente
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    con = sqlite3.connect('users.db')
    c = con.cursor()

    sucess_message, error_message = "", ""

    if request.method == 'POST':
        email = request.form['email']

        c.execute("SELECT full_name FROM users WHERE email=?", (email,))
        full_name = c.fetchone()[0]

        if verify_email(email):
            email_forgot_password(email, full_name)
            sucess_message = "Email enviado com sucesso"
        else:
            error_message = "Email inválido"

    con.close()
    return render_template('forgot_password.html', sucess_message=sucess_message, error_message=error_message)

@app.route('/recovery_password/<email>', methods=['GET', 'POST'])
def recovery_password(email):
    sucess_message, error_message = "", ""

    with sqlite3.connect('users.db') as con:
        c = con.cursor()

        if request.method == 'POST':
            password = request.form['password']
            conf_password = request.form['conf_password']

            c.execute("SELECT password FROM users WHERE email=?", (email,))
            result = c.fetchone()

            if not result:
                error_message = "Email não encontrado no sistema."
                return render_template('recovery_password.html', sucess_message=sucess_message, error_message=error_message)

            actual_password = result[0]

            if password == conf_password:
                if password != actual_password:  
                    c.execute("UPDATE users SET password=? WHERE email=?", (password, email))
                    con.commit()
                    sucess_message = "Senha alterada com sucesso!"
                else:
                    error_message = "A nova senha não pode ser igual à antiga."
            else:
                error_message = "As senhas devem ser iguais."

    return render_template('recovery_password.html', sucess_message=sucess_message, error_message=error_message)

def email_forgot_password(email, full_name):
    smtp_server = "smtp.gmail.com"
    port = 587  
    sender = "solidaria.gota@gmail.com"
    password = "hybd wqnw piyj ptzr"

    message = MIMEMultipart()
    message["Subject"] = "RECUPERAÇÃO DE SENHA"
    message["From"] = sender
    message["To"] = email

    html = f""" 
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px;">
            <table align="center" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; padding: 20px; border: 1px solid #ddd;">
                <tr>
                    <td style="padding: 20px; text-align: center; background-color: #ff0000; color: white; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                        <h1 style="margin: 0; font-size: 28px;">Gota Solidária</h1>
                        <p style="margin: 5px 0; font-size: 18px;">Sua ajuda é essencial, e estamos felizes em contar com você!</p>
                    </td>
                </tr>
                
                <tr>
                    <td style="padding: 20px;">
                        <p style="font-size: 18px;">Olá <strong>{full_name}</strong>,</p>
                        <p style="font-size: 18px;">Parece que voçê esqueceu sua senha, clique no botão abaixo para redefiní-la</p>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="http://127.0.0.1:5000/recovery_password/{email}" style="display: inline-block; padding: 12px 30px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">Redefina sua senha agora</a>
                        </p>
                        
                        <p style="font-size: 18px;">Estamos ansiosos para vê-lo novamente e agradecemos seu compromisso em salvar vidas.</p>

                        <p style="font-size: 18px;">Caso não queira redefinir a senha, ignore esta mensagem</p>
                        
                        <p style="font-size: 16px; color: #555; text-align: center; margin-top: 20px;">
                            Atenciosamente,<br>Equipe Gota Solidária
                        </p>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """
    message.attach(MIMEText(html, "html"))
    
    try:
        with smtplib.SMTP(smtp_server, port) as s:
            s.starttls()
            s.login(sender, password)
            s.sendmail(sender, email, message.as_string())
        return jsonify({"message": "Email enviado com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    add_clinicas()
    app.run(debug=True)
