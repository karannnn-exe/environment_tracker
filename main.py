from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import json
import os

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = 'karamazov'
ENV_FILE = 'environments.json'

# assumes you did not create a password for your database
# and the database username is the default, 'root'
# change if necessary
username = 'root'
password = 'root'
userpass = 'mysql+pymysql://' + username + ':' + password + '@'
server = 'localhost:3306'
# CHANGE to YOUR database name, with a slash added as shown
dbname = '/env_checkout'

app.config['SQLALCHEMY_DATABASE_URI'] = userpass + server + dbname
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'your_secret_key'  # Secret key for session management
# initialize the app with Flask-SQLAlchemy
db.init_app(app)


def load_environments():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_environments(environments):
    with open(ENV_FILE, 'w') as file:
        json.dump(environments, file, indent=4)


@app.route('/')
def start():
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("You must be logged in to access the dashboard!")
        return redirect(url_for('login'))
    environments = load_environments()
    return render_template('dashboard.html', username=session.get('username'), environments=environments)


@app.route('/db')
def testdb():
    try:
        query = text("SELECT * FROM env_info")
        result = db.session.execute(query).fetchall()
        print(result)
        # Convert the result to a list of dictionaries
        records = {row[0]: row[1] for row in result}
        print(records)
        return '<h1>It works.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text


# Route to display the login form
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')

        # Add your authentication logic here
        if user == 'admin' and pwd == 'password':  # Example credentials
            session['logged_in'] = True
            session['username'] = user
            query = text("update user_info set status = 'logged_in' where username = 'admin'")
            db.session.execute(query)
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password!")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clear the session
    user = request.form.get('username')
    query = text("update user_info set status = 'logged_out' where username = :user")
    db.session.execute(query, {'user': user})
    db.session.commit()
    return redirect(url_for('login'))


@app.route('/checkout/<env_name>', methods=['POST'])
def checkout(env_name):
    environments = load_environments()
    if env_name in environments:
        if environments[env_name]:
            flash(f'Environment {env_name} is already checked out.', 'warning')
        else:
            environments[env_name] = True
            save_environments(environments)
            flash(f'Checked out environment: {env_name}', 'success')
    else:
        flash(f'Environment {env_name} not found.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/return/<env_name>', methods=['POST'])
def return_env(env_name):
    environments = load_environments()
    if env_name in environments:
        if not environments[env_name]:
            flash(f'Environment {env_name} is already available.', 'warning')
        else:
            environments[env_name] = False
            save_environments(environments)
            flash(f'Returned environment: {env_name}', 'success')
    else:
        flash(f'Environment {env_name} not found.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/add', methods=['POST'])
def add_env():
    env_name = request.form['env_name']
    environments = load_environments()
    if env_name in environments:
        flash(f'Environment {env_name} already exists.', 'warning')
    else:
        environments[env_name] = False
        save_environments(environments)
        flash(f'Added environment: {env_name}', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
