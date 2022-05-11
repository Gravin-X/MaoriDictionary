from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
import datetime
import calendar
import smtplib, ssl
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_NAME = "realdictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret_name"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


def is_logged_in():
    """
    A function to return whether the user is logged in or not
    """
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


def is_teacher():
    """
    A function to return whether the user is a teacher or not
    """
    if not is_logged_in() or (session.get("teacher") is (None or 0)):
        print("Not teacher logged in")
        return False
    else:
        print("Teacher logged in")
        return True


def category_list():
    con = create_connection(DB_NAME)
    cur = con.cursor()
    query = "SELECT * FROM categories"
    cur.execute(query)
    queried_categories = cur.fetchall()
    con.close()
    return queried_categories


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


@app.route('/full_dictionary')
def render_full_dictionary():
    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT * FROM words"
    cur.execute(query)
    fetched_words = cur.fetchall()

    con.close()
    return render_template('full_dictionary.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_words=fetched_words, teacher_perms=is_teacher())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password)
        print(hashed_password)
        con = create_connection(DB_NAME)
        query = "SELECT id, first_name, password, teacher FROM user_details WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
            teacher = user_data[0][3]
        else:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['fname'] = first_name
        session['teacher'] = teacher
        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time')


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('teacher')

        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')
        print(password, len(password))
        if len(password) < 8:
            print(password, len(password), len(password) < 8)
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = "INSERT INTO user_details (first_name, last_name, email, password, teacher) VALUES(?,?,?,?,?)"

        cur = con.cursor()

        cur.execute(query, (fname, lname, email, hashed_password, teacher))  # executes the query

        con.commit()
        con.close()
        return redirect('/login')

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


@app.route('/word/<word_id>')
def render_word(word_id):
    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT * FROM words WHERE id = ?"
    cur.execute(query, (word_id,))
    queried_data = cur.fetchall()

    author = queried_data[0][1]

    print(queried_data)
    print(author)

    cur = con.cursor()
    query = "SELECT * FROM user_details WHERE id=?"
    cur.execute(query, (author,))
    user_list = cur.fetchall()

    con.close()
    return render_template('word.html', logged_in=is_logged_in(), category_list=category_list(),
                           word_data=queried_data, teacher_perms=is_teacher(), users=user_list)


@app.route('/category/<cat_id>')
def render_category(cat_id):
    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT id, category_names, user_created FROM categories WHERE id = ?"
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    cur = con.cursor()
    query = "SELECT * FROM words WHERE category_id = ?"
    cur.execute(query, (cat_id,))
    fetched_words = cur.fetchall()

    con.close()
    return render_template('category.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_data=fetched_categories, category_words=fetched_words,
                           teacher_perms=is_teacher())


@app.route('/add_word', methods=['GET', 'POST'])
def render_add_word_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    if request.method == 'POST':
        user_id = session.get('user_id')

        print(request.form)
        maori_word = request.form.get('maori').strip()
        english_translation = request.form.get('english').strip()
        year_level = request.form.get('level').strip()
        description = request.form.get('description').strip()
        category = request.form.get('category')

        con = create_connection(DB_NAME)

        query = "INSERT INTO words (id, maori, english, level, definition, user_id, timestamp, category_id, image) " \
                "VALUES(NULL,?,?,?,?,?,?,?,?)"

        cur = con.cursor()

        current_datetime = datetime.utcnow()
        current_timetuple = current_datetime.utctimetuple()
        current_timestamp = calendar.timegm(current_timetuple)
        timestamp = datetime.utcfromtimestamp(int(current_timestamp).strftime('%Y-%m-%d at %H:%M:%S'))

        try:
            cur.execute(query, (maori_word, english_translation, year_level, description, user_id, timestamp,
                                category, "noimage.png"))
        except ValueError:
            return redirect('/')

        con.commit()

        con.close()
        return redirect('/')

    return render_template('add_word.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_data=category_list(), teacher_perms=is_teacher())


@app.route('/add_category', methods=['GET', 'POST'])
def render_add_category_page():
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    if request.method == "POST":
        print(request.form)
        name = request.form.get('category_name')

        con = create_connection(DB_NAME)

        query = "INSERT INTO categories(id, category_names, user_created) VALUES(NULL,?,?)"

        cur = con.cursor()

        try:
            cur.execute(query, (name, 1))
        except ValueError:
            return redirect('/')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('add_category.html', category_list=category_list(), logged_in=is_logged_in(),
                           teacher_perms=is_teacher())


@app.route('/delete_category/<cat_id>')
def render_delete_category_page(cat_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT id, category_names FROM categories WHERE id = ?"
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    cur = con.cursor()
    query = "SELECT * FROM words WHERE category_id = ?"
    cur.execute(query, (cat_id,))
    fetched_words = cur.fetchall()

    con.close()

    return render_template('delete_category.html', category_data=fetched_categories, category_list=category_list(),
                           logged_in=is_logged_in(), category_words=fetched_words,
                           teacher_perms=is_teacher())


@app.route('/confirm_delete_category/<cat_id>')
def render_confirm_delete_category_page(cat_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    con = create_connection(DB_NAME)
    query = "DELETE FROM categories WHERE id = ?"

    cur = con.cursor()
    cur.execute(query, (cat_id,))

    con.commit()
    con.close()
    return redirect('/?Successfully+removed')


@app.route('/delete_word/<word_id>')
def render_delete_word_page(word_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT id, category_names FROM categories WHERE id = ?"
    cur.execute(query, (word_id,))
    fetched_categories = cur.fetchall()


    cur = con.cursor()
    query = "SELECT * FROM words WHERE id = ?"
    cur.execute(query, (word_id,))
    fetched_word = cur.fetchall()

    author = fetched_word[0][1]

    cur = con.cursor()
    query = "SELECT * FROM user_details WHERE id=?"
    cur.execute(query, (author,))
    user_list = cur.fetchall()

    con.close()

    return render_template('delete_word.html', category_data=fetched_categories, category_list=category_list(),
                           logged_in=is_logged_in(), word_data=fetched_word,
                           teacher_perms=is_teacher(), users=user_list)


@app.route('/confirm_delete_word/<word_id>')
def render_confirm_delete_word_page(word_id):

    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    con = create_connection(DB_NAME)
    query = "DELETE FROM words WHERE id = ?"

    cur = con.cursor()
    cur.execute(query, (word_id,))

    con.commit()
    con.close()
    return redirect('/?Successfully+removed')


app.run(host='0.0.0.0', debug=True)
