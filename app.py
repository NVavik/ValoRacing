from flask import Flask, render_template, request, redirect, url_for, g, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Для работы с сессиями
DATABASE = 'users.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                city TEXT,
                postal_code TEXT
            )
        ''')
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/reg', methods=['GET', 'POST'])
def regsign():
    if request.method == 'POST':
        try:
            user_data = {
                'first_name': request.form['firstName'],
                'last_name': request.form['lastName'],
                'username': request.form['username'],
                'email': request.form['email'],
                'password': hash_password(request.form['password']),  # Хешируем пароль
                'city': request.form.get('city', ''),
                'postal_code': request.form.get('postalCode', '')
            }

            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO users (first_name, last_name, username, email, password, city, postal_code)
                VALUES (:first_name, :last_name, :username, :email, :password, :city, :postal_code)
            ''', user_data)

            db.commit()
            session['message'] = 'Регистрация прошла успешно! Пожалуйста, войдите в систему.'
            return redirect(url_for('login'))  # Перенаправляем на вход после регистрации

        except sqlite3.IntegrityError as e:
            error = "Ошибка регистрации: "
            if 'UNIQUE constraint failed: users.username' in str(e):
                error += "Этот никнейм уже занят"
            elif 'UNIQUE constraint failed: users.email' in str(e):
                error += "Этот email уже используется"
            else:
                error += "Произошла ошибка в базе данных"

            return render_template('reg.html', error=error, form_data=request.form)

        except Exception as e:
            return render_template('reg.html',
                                   error=f"Ошибка сервера: {str(e)}",
                                   form_data=request.form)

    return render_template('reg.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''', (username, hash_password(password)))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']  # Сохраняем ID пользователя в сессии
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Неверные учетные данные")

    # Проверяем, есть ли сообщение об успешной регистрации
    message = session.pop('message', None)  # Извлекаем сообщение и удаляем его из сессии
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.clear()  # Очистка имени пользователя из сессии
    return redirect(url_for('index'))

@app.route('/bundles')
def bundles():
    return render_template('bundles.html')


@app.route('/wheelbase')
def wheelbase():
    return render_template('wheelbase.html')


@app.route('/wheels')
def wheels():
    return render_template('wheels.html')


@app.route('/pedals')
def pedals():
    return render_template('pedals.html')


@app.route('/addons')
def addons():
    return render_template('addons.html')


@app.route('/cockpits')
def cockpits():
    return render_template('cockpits.html')


@app.route('/equip')
def equip():
    return render_template('equip.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)