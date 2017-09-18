import gc

from flask import Flask, render_template, session, request, jsonify
from dbconnect import connect
from MySQLdb import escape_string as es
from passlib.hash import sha256_crypt as sha256

from dotmap import DotMap


c, dict_c, conn = connect()

app = Flask(__name__)
app.secret_key = "uhisfadvhgkjlfdsljhgblkjhgibdafslkjhgbdsfvhkbljdsfvkjhbdfsvkjhbdfscjhknl"

def escape_string(string):
    return es(string).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        email = escape_string(request.form['email'])
        passwd = request.form['passwd']

        # captcha_response = request.form['g-recaptcha-response']
        # if not checkRecaptcha(captcha_response, SECRET_KEY):
        #     return jsonify(error="Google recaptcha смяте, че сте робот.", code="4")

        x = dict_c.execute('select id, passwd from users where email = "%s";' % email)
        real_passwd = ""
        if not int(x):
            return jsonify(error="E-mail не е регистриран", code="2")
        
        fetched_info = DotMap(dict_c.fetchone())

        if not sha256.verify(passwd, fetched_info.passwd):
            return jsonify(error="Паролата не е вярна", code="3")
        
        session['logged_in'] = True
        session['client'] = True
        session['id'] = fetched_info.id
        
        gc.collect()
        
        return jsonify(code="1", url="/profile/")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        email = escape_string(request.form['email'])
        f_name = escape_string(request.form['f_name'])
        l_name = escape_string(request.form['l_name'])
        passwd = sha256.encrypt(request.form['passwd'])
        
        # captcha_response = request.form['g-recaptcha-response']
        # if not checkRecaptcha(captcha_response, SECRET_KEY):
        #     return jsonify(error="Google recaptcha смята, че сте робот.", code="3")

        x = c.execute('select * from users where email = "%s";' % email)
        if int(x):
            return jsonify(error="Email е зает!", code="2")
        
        c.execute('insert into users (email, f_name, l_name, passwd) values ("%s", "%s", "%s", "%s");' % (email, f_name, l_name, passwd))
        conn.commit()

        gc.collect()

        return jsonify(code="1", url="/login")

if __name__ == "__main__":
    app.run(debug=True, port=9000)