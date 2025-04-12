from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    conn = sqlite3.connect('project.db')
    c = conn.cursor()
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, user_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER,
                    description TEXT,
                    due_date TEXT,
                    priority TEXT,
                    status TEXT
                )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        c.execute("SELECT * FROM projects WHERE user_id=?", (session['user_id'],))
        projects = c.fetchall()
        conn.close()
        return render_template("index.html", projects=projects)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
            return redirect(url_for('register'))
        conn.close()
        flash("Registered successfully! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('project.db')
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, user_id) VALUES (?, ?)", (name, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template("add_project.html")

@app.route('/project/<int:project_id>', methods=['GET', 'POST'])
def view_project(project_id):
    conn = sqlite3.connect('project.db')
    c = conn.cursor()

    if request.method == 'POST':
        desc = request.form['desc']
        due = request.form['due']
        priority = request.form['priority']
        c.execute("INSERT INTO tasks (project_id, description, due_date, priority, status) VALUES (?, ?, ?, ?, ?)",
                  (project_id, desc, due, priority, "Pending"))
        conn.commit()

    c.execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id, session['user_id']))
    project = c.fetchone()

    c.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,))
    tasks = c.fetchall()

    conn.close()
    return render_template("view_project.html", project=project, tasks=tasks)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
