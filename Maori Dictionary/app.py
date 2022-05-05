from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime
import smtplib, ssl
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_NAME = "realdictionary.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "martyn"


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
    return render_template('home.html', logged_in=is_logged_in(), category_list=category_list())


@app.route('/full_dictionary')
def render_full_dictionary():
    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT * FROM words"
    cur.execute(query)
    fetched_words = cur.fetchall()

    con.close()
    return render_template('full_dictionary.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_words=fetched_words)


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password)
        print(hashed_password)
        con = create_connection(DB_NAME)
        query = "SELECT id, first_name, password FROM user_details WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
        else:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['fname'] = first_name
        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in(), category_list=category_list())


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

        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')
        print(password, len(password))
        if len(password) < 8:
            print(password, len(password), len(password) < 8)
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = "INSERT INTO user_details (first_name, last_name, email, password) VALUES(?,?,?,?)"

        cur = con.cursor()

        cur.execute(query, (fname, lname, email, hashed_password))  # executes the query
        con.commit()
        con.close()
        return redirect('/login')

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in(), category_list=category_list())


@app.route('/word/<word_id>')
def render_word(word_id):
    con = create_connection(DB_NAME)

    cur = con.cursor()
    query = "SELECT * FROM words WHERE id = ?"
    cur.execute(query, (word_id,))
    queried_data = cur.fetchall()

    con.close()
    return render_template('word.html', logged_in=is_logged_in(), category_list=category_list(),
                           word_data=queried_data)


@app.route('/category/<cat_id>')
def render_category(cat_id):
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
    return render_template('category.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_data=fetched_categories, category_words=fetched_words)


app.run(host='0.0.0.0', debug=True)
