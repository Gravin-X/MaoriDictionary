# Imports stuff
from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# Necessary code
DB_NAME = "realdictionary.db"
app = Flask(__name__)
app.secret_key = "secret_name"

# Bcrypt is used to hash the user's passwords.
bcrypt = Bcrypt(app)


# Creating a connection to the database
def create_connection(db_file):
    """
    Create a connection to the sqlite db
    """
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)

    return None


# Checks if the user is logged in
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


# Checks if the user is a teacher
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
    query = "SELECT * FROM categories"
    cur = con.cursor()
    cur.execute(query)
    queried_categories = cur.fetchall()
    con.close()
    return queried_categories


def get_word_data(word_id):
    con = create_connection(DB_NAME)

    query = "SELECT * FROM words WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    queried_data = cur.fetchall()

    print(queried_data)

    con.close()

    return queried_data


# Homepage
@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


# Full Dictionary
@app.route('/full_dictionary')
def render_full_dictionary():
    con = create_connection(DB_NAME)

    query = "SELECT * FROM words"
    cur = con.cursor()
    cur.execute(query)
    fetched_words = cur.fetchall()

    con.close()
    return render_template('full_dictionary.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_words=fetched_words, teacher_perms=is_teacher())


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    """
    Route for login page

    User enters login details
        - checks if they match details in user
            - if they do then login is successful - session is created
            -if not then error occurs - redirected to login page

    Returns login.html

    """
    # Redirects the user if logged in
    if is_logged_in():
        return redirect('/?error=Already+logged+in')
    # User enters login details
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

        # Checks if the user entries matches the login details
        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
            teacher = user_data[0][3]
        else:
            return redirect("/login?error=Email+or+password+is+incorrect")

        # Checks and compares the hashed password and entered password

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")
        # Creating Sessions
        session['email'] = email
        session['user_id'] = user_id
        session['fname'] = first_name
        session['teacher'] = teacher
        return redirect('/')
    # Error Prevention
    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('login.html', logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher(), error=error)


# Logout Route
@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time')


# Sign Up
@app.route('/signup', methods=['GET', 'POST'])

def render_signup_page():
    if is_logged_in():
        return redirect('/?error=Already+logged+in')

    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('teacher')

        # Checks if both passwords matches
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')
        # Checks whether the password is less than 8 characters
        if len(password) < 8:
            print(password, len(password), len(password) < 8)
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        # Hashes the password
        hashed_password = bcrypt.generate_password_hash(password)

        # Connects to the Database
        con = create_connection(DB_NAME)

        query = "INSERT INTO user_details (first_name, last_name, email, password, teacher) VALUES(?,?,?,?,?)"

        cur = con.cursor()

        # Executes the query
        cur.execute(query, (fname, lname, email, hashed_password, teacher))  # executes the query

        con.commit()
        con.close()
        return redirect('/login')

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


# Word
@app.route('/word/<word_id>', methods=['GET', 'POST'])
def render_word_page(word_id):
    if request.method == 'POST':
        if not is_logged_in():
            return redirect('/?error=Not+logged+in')

        if not is_teacher():
            return redirect('/?error=Not+teacher')

        user_id = session.get('user_id')

        # Current word data
        word_data = get_word_data(word_id)

        word_maori = word_data[0][3]
        word_english = word_data[0][4]
        word_desc = word_data[0][5]
        word_level = word_data[0][6]

        print(request.form)
        maori_word = request.form.get('maori').strip()
        english_translation = request.form.get('english').strip()
        year_level = request.form.get('level').strip()
        description = request.form.get('description').strip()
        timestamp = datetime.now()
        current_timestamp = timestamp.strftime("%Y-%m-%d %X")
        # category = request.form.get('category')

        year_level = max(0, min(10, int(year_level)))

        # date() #datetime.utcfromtimestamp(int(current_timestamp).strftime('%Y-%m-%d at %H:%M:%S'))

        if (word_maori != maori_word) or (word_english != english_translation) or (year_level != word_level) \
                or (word_desc != description):

            con = create_connection(DB_NAME)

            query = "UPDATE words SET user_id=?, maori=?, english=?, definition=?, level=?, timestamp=? WHERE id=?"

            cur = con.cursor()

            cur.execute(query, (user_id, maori_word, english_translation, description, year_level, current_timestamp,
                                word_id))

            # current_datetime = datetime.utcnow()
            # current_timetuple = current_datetime.utctimetuple()
            ##current_timestamp = calendar.timegm(current_timetuple)
            # timestamp = date() #datetime.utcfromtimestamp(int(current_timestamp).strftime('%Y-%m-%d at %H:%M:%S'))

            # try:
            #    cur.execute(query, (maori_word, english_translation, year_level, description, user_id, timestamp,
            #                        category, "noimage.png", word_id))
            # except ValueError:
            #    return redirect('/')

            con.commit()

            con.close()
        else:
            return redirect('/word/' + str(word_id) + "?error=Nothing+changed")
        return redirect('/word/' + str(word_id))
    else:
        con = create_connection(DB_NAME)

        query = "SELECT * FROM words WHERE id = ?"
        cur = con.cursor()
        cur.execute(query, (word_id,))
        queried_data = cur.fetchall()

        print(queried_data)

        author = queried_data[0][1]

        print(queried_data)
        print(author)

        query = "SELECT * FROM user_details WHERE id=?"
        cur = con.cursor()
        cur.execute(query, (author,))
        user_list = cur.fetchall()

        con.close()
    return render_template('word.html', logged_in=is_logged_in(), category_list=category_list(),
                           word_data=queried_data, teacher_perms=is_teacher(), users=user_list)


# Category
@app.route('/category/<cat_id>')
def render_category_page(cat_id):
    con = create_connection(DB_NAME)

    query = "SELECT id, category_names, user_created FROM categories WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    query = "SELECT * FROM words WHERE category_id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_words = cur.fetchall()

    con.close()
    return render_template('category.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_data=fetched_categories, category_words=fetched_words,
                           teacher_perms=is_teacher())


# Add Word
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

        year_level = max(0, min(10, int(year_level)))

        con = create_connection(DB_NAME)

        query = "INSERT INTO words (id, maori, english, level, definition, user_id, timestamp, category_id, image) " \
                "VALUES(NULL,?,?,?,?,?,date(),?,?)"

        cur = con.cursor()

        try:
            cur.execute(query, (maori_word, english_translation, year_level, description, user_id, category,
                                "noimage.png"))
        except ValueError:
            return redirect('/')

        con.commit()

        con.close()
        return redirect('/')

    return render_template('add_word.html', logged_in=is_logged_in(),
                           category_list=category_list(), teacher_perms=is_teacher())


# Add Category
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
        except sqlite3.IntegrityError:
            return redirect('/?error=This+category+already+exists')
        con.commit()
        con.close()

        # Error Prevention
    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('add_category.html', error=error, category_list=category_list(), logged_in=is_logged_in(),
                           teacher_perms=is_teacher())


# Delete Category
@app.route('/delete_category/<cat_id>')
def render_delete_category_page(cat_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Not+teacher')

    con = create_connection(DB_NAME)

    query = "SELECT id, category_names FROM categories WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    query = "SELECT * FROM words WHERE category_id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_words = cur.fetchall()

    con.close()

    return render_template('delete_category.html', category_data=fetched_categories, category_list=category_list(),
                           logged_in=is_logged_in(), category_words=fetched_words,
                           teacher_perms=is_teacher())


# Confirm Delete Category
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


# Delete Word
@app.route('/delete_word/<word_id>')
def render_delete_word_page(word_id):
    if is_logged_in():
        if not is_teacher():
            return redirect('/?error=Not+teacher')

        con = create_connection(DB_NAME)

        query = "SELECT id, category_names FROM categories WHERE id = ?"
        cur = con.cursor()
        cur.execute(query, (word_id,))
        fetched_categories = cur.fetchall()

        query = "SELECT * FROM words WHERE id = ?"
        cur = con.cursor()
        cur.execute(query, (word_id,))
        fetched_word = cur.fetchall()

        author = fetched_word[0][1]

        query = "SELECT * FROM user_details WHERE id=?"
        cur = con.cursor()
        cur.execute(query, (author,))
        user_list = cur.fetchall()

        con.close()

        return render_template('delete_word.html', category_data=fetched_categories, category_list=category_list(),
                               logged_in=is_logged_in(), word_data=fetched_word,
                               teacher_perms=is_teacher(), users=user_list)

    return redirect('/?error=Not+logged+in')


# Confirm Delete Word
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
