# *-* coding: utf-8 *-*
import gc
import json
import os

from datetime import datetime

from flask import Flask, render_template, session, request, jsonify, redirect, make_response
from dbconnect import connect
from MySQLdb import escape_string as es
from passlib.hash import sha256_crypt as sha256

from dotmap import DotMap

from functools import wraps, update_wrapper
from shutil import copyfile

c, dict_c, conn = connect()

app = Flask(__name__)
app.secret_key = "uhisfadvhgkjlfdsljhgblkjhgibdafslkjhgbdsfvhkbljdsfvkjhbdfsvkjhbdfscjhknl"

UPLOAD_FOLDER = "{}/static/img/profile_pics".format(os.path.dirname(os.path.realpath(__file__))) # "~/Desktop/proj/SConnect/static/img/profile_pics"

def escape_string(string):
    return es(string).decode('utf-8')

def dict_l_to_dotmap(l):
    res = []
    for i in l:
        res.append(DotMap(i))
    return res

def login_req(f):
    @wraps(f)
    def wrap(*a, **kw):
        if 'logged_in' in session:
            return f(*a, **kw)
        else:
            return redirect('/login')

    return wrap

def no_cache(f):
    @wraps(f)
    def wrap(*a, **kw):
        response = make_response(f(*a, **kw))
        response.headers["Last-Modified"] = datetime.now()
        response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers['Pragma'] = "no-cache"
        response.headers["Expires"] = "-1"

        return response
    return update_wrapper(wrap, f)

@app.route('/')
def index():
    return render_template('loginregister.html')

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
        session['id'] = fetched_info.id

        gc.collect()

        return jsonify(code = "1", url = "/home")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        email = escape_string(request.form['email'])
        f_name = escape_string(request.form['f_name'])
        l_name = escape_string(request.form['l_name'])
        passwd = sha256.encrypt(request.form['passwd'])
        school = escape_string(request.form['school'])

        # captcha_response = request.form['g-recaptcha-response']
        # if not checkRecaptcha(captcha_response, SECRET_KEY):
        #     return jsonify(error="Google recaptcha смята, че сте робот.", code="3")

        x = c.execute('select * from users where email = "%s";' % email)
        if int(x):
            return jsonify(error="Email е зает!", code="2")

        c.execute('insert into users (email, f_name, l_name, passwd, school) values ("%s", "%s", "%s", "%s", "%s");' % (email, f_name, l_name, passwd, school))
        conn.commit()

        gc.collect()

        dict_c.execute('select id from users where email = "{}";'.format(email))
        id = dict_c.fetchone()['id']

        copyfile('{}/default.png'.format(UPLOAD_FOLDER), '{0}/{1}.png'.format(UPLOAD_FOLDER, id))

        return jsonify(code="1", url="/login")

@app.route('/home')
@no_cache
def home():

    return render_template('home1.html',)

@app.route('/settings', methods=["GET", "POST"])
@no_cache
def settings():
    if request.method == "GET":
        dict_c.execute('select * from interests;')
        interests = dict_l_to_dotmap(dict_c.fetchall())

        c.execute('select interests from users where id = {};'.format(session['id']))
        try:
            user_interests = json.loads(c.fetchone()[0])
        except Exception:
            user_interests = []
        return render_template('settings.html', interests=interests, user_interests=user_interests, str=str)
    else:
        if 'profile_pic' in request.files:
            f = request.files['profile_pic']
            if f.filename != "":
                #if the file exists, delete it and replace it with a new one
                if '{}.png'.format(session['id']) in os.listdir(UPLOAD_FOLDER):
                    os.remove("{0}/{1}.png".format(UPLOAD_FOLDER, session['id']))
                f.save("{0}/{1}.png".format(UPLOAD_FOLDER, session['id']))
                print("file save")

        interests = list(dict(request.form).keys())
        print(interests)

        c.execute('update users set interests = "{0}" where id = {1};'.format(escape_string(json.dumps(interests)), session['id']))
        conn.commit()

        return redirect('/home')

@app.route('/add-interest', methods=["POST"])
def add_interest():
    name = escape_string(request.form['name'])

    x = c.execute('select * from interests where name = "{}";'.format(name))
    if int(x):
        return redirect('/settings')

    c.execute('insert into interests (name) values ("{}");'.format(name))
    conn.commit()

    return redirect('/home')

@app.route('/find-friends')
def find_friends():
    c.execute('select interests from users where id = {};'.format(session['id']))
    interests = json.loads(c.fetchone()[0])
    interest_objs = []

    for interest in interests:
        dict_c.execute('select * from interests where id = {}'.format(interest))
        res = DotMap(interest = DotMap(dict_c.fetchone()))

        dict_c.execute('select f_name, l_name, id from users where cast(interests as char) like "%{0}%" and id != {1};'.format(res.interest.id, session['id']))
        res.users = dict_l_to_dotmap(dict_c.fetchall())

        print(res)
        interest_objs.append(res)

    return render_template('find_friends.html', interest_objs=interest_objs)

@app.route('/send-friend-request/<int:uid>')
def friend_req(uid):
    x = c.execute('select * from friendships where (person_1 = {0} or person_1 = {1}) and (person_2 = {0} or person_2 = {1});'.format(session['id'], uid))
    if int(x):
        return redirect('/find-friends')

    c.execute('insert into friendships (person_1, person_2, status) values ({0}, {1}, 0)'.format(session['id'], uid))
    conn.commit()

    return redirect('/home')

@app.route('/notifications')
def notify():
    c.execute('select person_1 from friendships where person_2 = {} and status = 0;'.format(session['id']))
    notif_ids = [el[0] for el in c.fetchall()]
    if len(notif_ids) == 0:
        return render_template('notifications.html', notifications=[])

    notifications = []

    for notif in notif_ids:
        dict_c.execute('select f_name, l_name, id from users where id = {};'.format(notif))
        res = DotMap(dict_c.fetchone())
        notifications.append(res)

    return render_template('notifications.html', notifications=notifications)

@app.route('/accept/<int:uid>')
def accept(uid):
    c.execute('update friendships set status = 1 where person_1 = {0} and person_2 = {1}'.format(uid, session['id']))
    conn.commit()
    return redirect('/home')

@app.route('/friends')
def friends():
    c.execute('select if(person_1 = {0}, person_2, person_1) as person from friendships where (person_1 = {0} or person_2 = {0}) and status = 1;'.format(session['id']))
    friend_ids = [el[0] for el in c.fetchall()]

    friends = []

    for fid in friend_ids:
        dict_c.execute('select f_name, l_name, id from users where id = {};'.format(fid))
        res = DotMap(dict_c.fetchone())
        friends.append(res)

    return render_template('friends.html', friends=friends)

if __name__ == "__main__":
    app.run(debug=True, port=9000)
