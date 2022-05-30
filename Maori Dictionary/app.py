# Imports modules
from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# Necessary code
DB_NAME = "realdictionary.db"
app = Flask(__name__)
app.secret_key = "sage"

# Bcrypt is used to hash the user's passwords.
bcrypt = Bcrypt(app)


# Functions

# Creating a connection to the database
def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
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
    """
    A function to return all the categories ordered by their alphabetical order
    """
    # Connects to the Database
    con = create_connection(DB_NAME)
    query = "SELECT * FROM categories ORDER BY category_names ASC"
    # Creates a cursor to write the query
    cur = con.cursor()
    cur.execute(query)
    # Fetches the data
    queried_categories = cur.fetchall()
    con.close()
    return queried_categories


def get_word_data(word_id):
    """
    A function to return all the words
    """
    # Connects to the Database
    con = create_connection(DB_NAME)

    query = "SELECT * FROM words WHERE id = ?"
    # Creates a cursor to write the query
    cur = con.cursor()
    # Executes the query
    cur.execute(query, (word_id,))
    # Fetches the data
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
    # Connects to the Database
    con = create_connection(DB_NAME)

    query = "SELECT * FROM words"
    # Creates a cursor to write the query
    cur = con.cursor()
    # Executes the query
    cur.execute(query)
    # Fetches the data
    fetched_words = cur.fetchall()

    con.close()
    return render_template('full_dictionary.html', logged_in=is_logged_in(), category_list=category_list(),
                           category_words=fetched_words, teacher_perms=is_teacher())


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    # Redirects to the homepage, if the user is logged in
    if is_logged_in():
        return redirect('/?error=Already+logged+in')
    # User enters login details
    if request.method == 'POST':
        print(request.form)
        # Gets inputted data from the form
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        # Hashes the password
        hashed_password = bcrypt.generate_password_hash(password)
        print(hashed_password)
        # Connects to the Database
        con = create_connection(DB_NAME)
        query = "SELECT id, first_name, password, teacher FROM user_details WHERE email=?"
        # Creates a cursor to write the query
        cur = con.cursor()
        # Executes the query
        cur.execute(query, (email,))
        # Fetches the data
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
    # Display errors to the user
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
    # Redirects to the homepage, if the user is logged in
    if is_logged_in():
        return redirect('/?error=Already+logged+in')
    # Runs the code if the user submits the form
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
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

        # Builds user data in order to add to the database
        query = "INSERT INTO user_details (first_name, last_name, email, password, teacher) VALUES(?,?,?,?,?)"

        # Creates a cursor to write the query
        cur = con.cursor()

        # Executes the query
        try:
            cur.execute(query, (fname, lname, email, hashed_password, teacher))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        # Commit and close database connection
        con.commit()
        con.close()

        # Redirects to the login page
        return redirect('/login')

    # Displays error to the user
    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in(), category_list=category_list(),
                           teacher_perms=is_teacher())


# Word
@app.route('/word/<word_id>', methods=['GET', 'POST'])
def render_word_page(word_id):
    if request.method == 'POST':
        # Redirects to the homepage, if the user isn't logged in
        if not is_logged_in():
            return redirect('/?error=Not+logged+in')
        # Redirects to the homepage, if the user isn't a teacher
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
        # Gets the data from the form
        maori_word = request.form.get('maori').strip()
        english_translation = request.form.get('english').strip()
        year_level = int(request.form.get('level'))
        description = request.form.get('description').strip()
        timestamp = datetime.now()
        print(word_maori)
        print(word_english)
        print(word_desc)
        print(word_level)
        # Only updates if any values has been changed
        if (word_maori != maori_word) or (word_english != english_translation) or (year_level != word_level) \
                or (word_desc != description):

            # Connects to the Database
            con = create_connection(DB_NAME)

            # Collects the new data so the details can be updated
            query = "UPDATE words SET user_id=?, maori=?, english=?, definition=?, level=?, timestamp=? WHERE id=? "

            # Creates a cursor to write the query
            cur = con.cursor()

            cur.execute(query, (user_id, maori_word, english_translation, description, year_level, timestamp,
                                word_id))

            # Commits and closes the
            con.commit()
            con.close()
        else:
            return redirect('/word/' + str(word_id) + "?error=Nothing+changed")
        return redirect('/word/' + str(word_id))
    else:
        # Connects to the Database
        con = create_connection(DB_NAME)

        query = "SELECT * FROM words WHERE id = ?"
        # Creates a cursor to write the query
        cur = con.cursor()
        cur.execute(query, (word_id,))
        queried_data = cur.fetchall()

        print(queried_data)
        if not queried_data:
            return redirect('/?error=Word+doesnt+exist')

        author = queried_data[0][1]

        print(author)

        query = "SELECT * FROM user_details WHERE id=?"
        # Creates a cursor to write the query
        cur = con.cursor()
        cur.execute(query, (author,))
        user_list = cur.fetchall()

        con.close()
    return render_template('word.html', logged_in=is_logged_in(), category_list=category_list(),
                           word_data=queried_data, teacher_perms=is_teacher(), users=user_list)


# Category
@app.route('/category/<cat_id>')
def render_category_page(cat_id):
    # Connects to the Database
    con = create_connection(DB_NAME)

    query = "SELECT id, category_names, user_created FROM categories WHERE id = ?"
    # Creates a cursor to write the query
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    query = "SELECT * FROM words WHERE category_id = ? ORDER BY maori ASC"
    # Creates a cursor to write the query
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
    # Redirects to the homepage if the user is not logged in
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    # Redirects to the homepage if the user is not a teacher
    if not is_teacher():
        return redirect('/?error=Not+teacher')
    # Runs the code if the user adds a new word
    if request.method == 'POST':
        user_id = session.get('user_id')

        print(request.form)
        # Gets the data from the add word form
        maori_word = request.form.get('maori').strip().lower()
        english_translation = request.form.get('english').strip().lower()
        year_level = request.form.get('level').strip()
        description = request.form.get('description').strip()
        category = request.form.get('category')

        year_level = max(0, min(10, int(year_level)))

        # Connects to the database
        con = create_connection(DB_NAME)

        # Checks to see if there are any duplicated words
        query = "SELECT english FROM words WHERE english=?"

        # Creates a cursor to write the query
        cur = con.cursor()
        # Executes the query
        cur.execute(query, (english_translation,))
        # Fetches the data
        duplicate_words = cur.fetchall()

        # If the length of the list is above zero then it will detect that
        if len(duplicate_words) > 0:
            return redirect('/add_word?error=Word+already+exists')

        # Builds the new word data in order to add to the database
        query = "INSERT INTO words (id, maori, english, level, definition, user_id, timestamp, category_id, image) " \
                "VALUES(NULL,?,?,?,?,?,?,?,?)"

        # Creates a cursor to write the query
        cur = con.cursor()

        # Error prevention
        try:
            # Executes the query and inserts into the words table
            cur.execute(query, (maori_word, english_translation, year_level, description, user_id, datetime.now(),
                                category, "noimage.png"))
        except ValueError:
            return redirect('/')

        # Commit and close database connection
        con.commit()
        con.close()

        return redirect('/')

    # Displays error to the user
    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('add_word.html', error=error, logged_in=is_logged_in(),
                           category_list=category_list(), teacher_perms=is_teacher())


# Add Category
@app.route('/add_category', methods=['GET', 'POST'])
def render_add_category_page():
    # Redirects to the homepage, if the user isn't logged in
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    # Redirects to the homepage, if the user isn't a teacher
    if not is_teacher():
        return redirect('/?error=Not+teacher')
    # Runs the code if the user adds a new category
    if request.method == "POST":
        print(request.form)
        name = request.form.get('category_name').strip().title()

        # Connects to the database
        con = create_connection(DB_NAME)

        # Builds new category in order to add to the database
        query = "INSERT INTO categories(id, category_names, user_created) VALUES(NULL,?,?)"

        # Creates a cursor to write the query
        cur = con.cursor()

        # Error prevention
        try:
            # Executes the query and inserts into the category table
            cur.execute(query, (name, 1))
        except sqlite3.IntegrityError:
            return redirect('?error=This+category+already+exists')
        # Commit and close database connection
        con.commit()
        con.close()

    # Display error to the user
    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('add_category.html', error=error, category_list=category_list(), logged_in=is_logged_in(),
                           teacher_perms=is_teacher())


# Delete Category
@app.route('/delete_category/<cat_id>')
def render_delete_category_page(cat_id):
    # Redirects to the homepage, if the user isn't logged in
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    # Redirects to the homepage, if the user isn't a teacher
    if not is_teacher():
        return redirect('/?error=Not+teacher')

    # Connects to the database
    con = create_connection(DB_NAME)

    query = "SELECT id, category_names FROM categories WHERE id = ?"
    # Creates a cursor to write the query
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    fetched_categories = cur.fetchall()

    if not fetched_categories:
        return redirect('/?error=No+such+category')

    query = "SELECT * FROM words WHERE category_id = ?"
    # Creates a cursor to write the query
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
    # Redirects to the homepage, if the user isn't logged in
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    # Redirects to the homepage, if the user isn't a teacher
    if not is_teacher():
        return redirect('/?error=Not+teacher')

    # Connects to the database
    con = create_connection(DB_NAME)
    query = "DELETE FROM categories WHERE id = ?"
    # Creates a cursor to write the query
    cur = con.cursor()
    cur.execute(query, (cat_id,))

    con.commit()
    con.close()
    return redirect('/?Category+successfully+removed')


# Delete Word
@app.route('/delete_word/<word_id>')
def render_delete_word_page(word_id):
    if is_logged_in():
        if not is_teacher():
            return redirect('/?error=Not+teacher')

        # Connects to the database
        con = create_connection(DB_NAME)

        query = "SELECT id, category_names FROM categories WHERE id = ?"
        # Creates a cursor to write the query
        cur = con.cursor()
        cur.execute(query, (word_id,))
        fetched_categories = cur.fetchall()

        query = "SELECT * FROM words WHERE id = ?"
        # Creates a cursor to write the query
        cur = con.cursor()
        cur.execute(query, (word_id,))
        fetched_word = cur.fetchall()

        if not fetched_word:
            return redirect('/?error=Word+doesnt+exist')

        author = fetched_word[0][1]

        query = "SELECT * FROM user_details WHERE id=?"
        # Creates a cursor to write the query
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
    # Redirects to the homepage, if the user isn't logged in
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    # Redirects to the homepage, if the user isn't a teacher
    if not is_teacher():
        return redirect('/?error=Not+teacher')

    # Connects to the database
    con = create_connection(DB_NAME)

    # Finds words that has the detonated id
    query = "DELETE FROM words WHERE id = ?"

    # Creates a cursor to write the query
    cur = con.cursor()

    # Executes the query and deletes the selected word from the words table
    cur.execute(query, (word_id,))

    # Commit and close database connection
    con.commit()
    con.close()

    # Redirects to the homepage and lets the user know that the word was successfully removed
    return redirect('/?Word+successfully+removed')


app.run(host='0.0.0.0', debug=True)
