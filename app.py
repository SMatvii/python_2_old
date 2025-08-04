from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import bcrypt
import requests
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

WEATHER_API_KEY = 'your-api-key-here'
WEATHER_API_URL = 'http://api.openweathermap.org/data/2.5/weather'

def init_db():
    """Ініціалізація бази даних"""
    conn = sqlite3.connect('school_schedule.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            teacher TEXT NOT NULL,
            classroom TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            time_start TEXT NOT NULL,
            time_end TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject TEXT NOT NULL,
            due_date DATE,
            completed BOOLEAN DEFAULT FALSE,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            test_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('school_schedule.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_weather(city='Kyiv'):
    try:
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'uk'
        }
        response = requests.get(WEATHER_API_URL, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Помилка отримання погоди: {e}")
        return None

@app.route('/')
def index():
    weather_data = get_weather()
    return render_template('index.html', weather=weather_data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'student')
        
        if not username or not email or not password:
            flash('Всі поля обов\'язкові для заповнення')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('Користувач з таким ім\'ям або email вже існує')
            conn.close()
            return render_template('register.html')
        
        password_hash = hash_password(password)
        conn.execute(
            'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
            (username, email, password_hash, role)
        )
        conn.commit()
        conn.close()
        
        send_registration_email(email, username)
        
        flash('Реєстрація успішна! Перевірте свій email.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Вхід успішний!')
            return redirect(url_for('index'))
        else:
            flash('Невірні дані для входу')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Ви вийшли з системи')
    return redirect(url_for('index'))

@app.route('/schedule')
@login_required
def schedule():
    conn = get_db_connection()
    lessons = conn.execute(
        'SELECT * FROM lessons ORDER BY day_of_week, time_start'
    ).fetchall()
    conn.close()
    
    schedule_by_day = {}
    days = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця']
    
    for day in days:
        schedule_by_day[day] = [lesson for lesson in lessons if lesson['day_of_week'] == day]
    
    return render_template('schedule.html', schedule=schedule_by_day)

@app.route('/add_lesson', methods=['GET', 'POST'])
@login_required
def add_lesson():
    if session.get('role') not in ['admin', 'teacher']:
        flash('У вас немає прав для додавання уроків')
        return redirect(url_for('schedule'))
    
    if request.method == 'POST':
        subject = request.form['subject']
        teacher = request.form['teacher']
        classroom = request.form['classroom']
        day_of_week = request.form['day_of_week']
        time_start = request.form['time_start']
        time_end = request.form['time_end']
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO lessons (subject, teacher, classroom, day_of_week, time_start, time_end, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (subject, teacher, classroom, day_of_week, time_start, time_end, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        flash('Урок успішно додано!')
        return redirect(url_for('schedule'))
    
    return render_template('add_lesson.html')

@app.route('/tasks')
@login_required
def tasks():
    conn = get_db_connection()
    user_tasks = conn.execute(
        'SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('tasks.html', tasks=user_tasks)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO tasks (title, description, subject, due_date, user_id) VALUES (?, ?, ?, ?, ?)',
        (data['title'], data['description'], data['subject'], data['due_date'], session['user_id'])
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Завдання додано!'})

@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM tasks WHERE id = ? AND user_id = ?',
        (task_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Завдання видалено!'})

@app.route('/delete_lesson/<int:lesson_id>', methods=['DELETE'])
@login_required
def delete_lesson(lesson_id):
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'success': False, 'message': 'У вас немає прав для видалення уроків'})
    
    conn = get_db_connection()
    conn.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Урок видалено!'})

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/submit_test', methods=['POST'])
def submit_test():
    data = request.get_json()
    score = data.get('score', 0)
    total = data.get('total', 0)
    
    if 'user_id' in session:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO test_results (user_id, test_name, score, total_questions) VALUES (?, ?, ?, ?)',
            (session['user_id'], 'Загальний тест', score, total)
        )
        conn.commit()
        conn.close()
    
    return jsonify({'success': True, 'score': score, 'total': total})

def send_registration_email(email, username):
    try:
        print(f"Відправка email на {email} для користувача {username}")
        return True
    except Exception as e:
        print(f"Помилка відправки email: {e}")
        return False

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
