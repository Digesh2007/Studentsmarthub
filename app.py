from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'studenthub.db'

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-strong-secret'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        pw_hash=generate_password_hash(password)
        db=get_db()
        try:
            db.execute('INSERT INTO users (name,email,password) VALUES (?,?,?)',(name,email,pw_hash))
            db.commit()
            flash('Registration successful. Please log in.','success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.','danger')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        db=get_db()
        cur=db.execute('SELECT * FROM users WHERE email=?',(email,))
        user=cur.fetchone()
        if user and check_password_hash(user['password'],password):
            session['user_id']=user['id']
            session['user_name']=user['name']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['user_name'])

@app.route('/notes')
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db=get_db()
    cur=db.execute('SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],))
    return render_template('notes.html', notes=cur.fetchall())

@app.route('/notes/add', methods=['GET','POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        title=request.form['title']
        content=request.form['content']
        db=get_db()
        db.execute('INSERT INTO notes (user_id,title,content) VALUES (?,?,?)',(session['user_id'],title,content))
        db.commit()
        flash('Note added','success')
        return redirect(url_for('notes'))
    return render_template('add_note.html')

@app.route('/notes/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db=get_db()
    db.execute('DELETE FROM notes WHERE id=? AND user_id=?',(note_id,session['user_id']))
    db.commit()
    flash('Note deleted','info')
    return redirect(url_for('notes'))

if __name__=='__main__':
    app.run(debug=True)
