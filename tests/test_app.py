import pytest
import sqlite3
import tempfile
import os
from app import app, init_db, hash_password, check_password

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def auth(client):
    class AuthActions:
        def __init__(self, client):
            self._client = client
        
        def login(self, username='testuser', password='testpass'):
            return self._client.post('/login', data={
                'username': username,
                'password': password
            })
        
        def logout(self):
            return self._client.get('/logout')
        
        def register(self, username='testuser', email='test@example.com', 
                    password='testpass', role='student'):
            return self._client.post('/register', data={
                'username': username,
                'email': email,
                'password': password,
                'role': role
            })
    
    return AuthActions(client)

class TestAuthentication:   
    def test_register_user(self, client, auth):
        rv = client.get('/register')
        assert rv.status_code == 200
        assert b'registration' in rv.data.lower() or 'реєстрація'.encode('utf-8') in rv.data
        
        rv = auth.register()
        assert rv.status_code == 302
        
        with sqlite3.connect('school_schedule.db') as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', ('testuser',)
            ).fetchone()
            assert user is not None
    
    def test_register_duplicate_user(self, client, auth):
        rv = auth.register()
        assert 'користувач'.encode('utf-8') in rv.data.lower() and 'існує'.encode('utf-8') in rv.data.lower()
    
    def test_login_valid_user(self, client, auth):
        auth.register()
        rv = auth.login()
        assert rv.status_code == 302
        with client.session_transaction() as sess:
            assert 'user_id' in sess
    
    def test_login_invalid_user(self, client, auth):
        rv = auth.login('wronguser', 'wrongpass')
        assert 'невірні'.encode('utf-8') in rv.data.lower() or b'incorrect' in rv.data.lower()
    
    def test_logout(self, client, auth):
        auth.register()
        auth.login()
        
        rv = auth.logout()
        assert rv.status_code == 302
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

class TestPasswordSecurity:
    
    def test_password_hashing(self):
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password.encode('utf-8')
        assert check_password(password, hashed) == True
        assert check_password("wrongpassword", hashed) == False
    
    def test_password_length_validation(self, client):
        short_password = "123"
        rv = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': short_password,
            'role': 'student'
        })
        
class TestSchedule:
    
    def test_schedule_requires_login(self, client):
        rv = client.get('/schedule')
        assert rv.status_code == 302
    
    def test_add_lesson_requires_permission(self, client, auth):
        auth.register(role='student')
        auth.login()
        
        rv = client.get('/add_lesson')
        assert rv.status_code == 302 or 'немає прав'.encode('utf-8') in rv.data.lower()
    
    def test_add_lesson_as_teacher(self, client, auth):
        auth.register(role='teacher')
        auth.login()
        
        rv = client.get('/add_lesson')
        assert rv.status_code == 200
        
        rv = client.post('/add_lesson', data={
            'subject': 'Математика',
            'teacher': 'Іванов І.І.',
            'classroom': '101',
            'day_of_week': 'Понеділок',
            'time_start': '08:00',
            'time_end': '09:35'
        })
        assert rv.status_code == 302
        with sqlite3.connect('school_schedule.db') as conn:
            lesson = conn.execute(
                'SELECT * FROM lessons WHERE subject = ?', ('Математика',)
            ).fetchone()
            assert lesson is not None

class TestTasks:
    def test_tasks_require_login(self, client):
        rv = client.get('/tasks')
        assert rv.status_code == 302
    
    def test_add_task_api(self, client, auth):
        auth.register()
        auth.login()
        
        rv = client.post('/add_task', 
                        json={
                            'title': 'Тестове завдання',
                            'description': 'Опис завдання',
                            'subject': 'Математика',
                            'due_date': '2025-12-31'
                        },
                        content_type='application/json')
        
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] == True
    
    def test_delete_task_api(self, client, auth):
        auth.register()
        auth.login()
        with sqlite3.connect('school_schedule.db') as conn:
            conn.execute(
                'INSERT INTO tasks (title, subject, user_id) VALUES (?, ?, ?)',
                ('Тест завдання', 'Математика', 1)
            )
            conn.commit()
            task_id = conn.lastrowid
        
        rv = client.delete(f'/delete_task/{task_id}')
        assert rv.status_code == 200
        data = rv.get_json()
        assert data['success'] == True

class TestTest:
    def test_test_page_accessible(self, client):
        rv = client.get('/test')
        assert rv.status_code == 200
        assert b'test' in rv.data.lower() or 'тест'.encode('utf-8') in rv.data
    
    def test_submit_test_results(self, client, auth):
        rv = client.post('/submit_test',
                        json={'score': 8, 'total': 10},
                        content_type='application/json')
        assert rv.status_code == 200
        
        auth.register()
        auth.login()
        
        rv = client.post('/submit_test',
                        json={'score': 8, 'total': 10},
                        content_type='application/json')
        assert rv.status_code == 200
        
        with sqlite3.connect('school_schedule.db') as conn:
            result = conn.execute(
                'SELECT * FROM test_results WHERE user_id = ?', (1,)
            ).fetchone()
            assert result is not None

class TestSQLInjection:
    
    def test_sql_injection_in_login(self, client):
        malicious_input = "'; DROP TABLE users; --"
        
        rv = client.post('/login', data={
            'username': malicious_input,
            'password': 'anypassword'
        })
        
        with sqlite3.connect('school_schedule.db') as conn:
            try:
                conn.execute('SELECT COUNT(*) FROM users').fetchone()
                assert True
            except sqlite3.OperationalError:
                assert False, "SQL injection vulnerability detected!"
    
    def test_sql_injection_in_tasks(self, client, auth):
        auth.register()
        auth.login()
        
        malicious_input = "'; DROP TABLE tasks; --"
        
        rv = client.post('/add_task',
                        json={
                            'title': malicious_input,
                            'description': 'Test',
                            'subject': 'Test',
                            'due_date': '2025-12-31'
                        },
                        content_type='application/json')
        
        with sqlite3.connect('school_schedule.db') as conn:
            try:
                conn.execute('SELECT COUNT(*) FROM tasks').fetchone()
                assert True
            except sqlite3.OperationalError:
                assert False, "SQL injection vulnerability in tasks!"

class TestInputValidation:
    
    def test_empty_form_submission(self, client):
        rv = client.post('/register', data={
            'username': '',
            'email': '',
            'password': '',
            'role': 'student'
        })
        assert 'обов\'язкові'.encode('utf-8') in rv.data.lower() or rv.status_code != 302
    
    def test_invalid_email_format(self, client):
        rv = client.post('/register', data={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'testpass',
            'role': 'student'
        })
        with sqlite3.connect('school_schedule.db') as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', ('testuser',)
            ).fetchone()

class TestDatabase:
    
    def test_database_initialization(self, client):
        with sqlite3.connect('school_schedule.db') as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            table_names = [table[0] for table in tables]
            required_tables = ['users', 'lessons', 'tasks', 'test_results']
            
            for table in required_tables:
                assert table in table_names
    
    def test_user_creation_and_retrieval(self, client, auth):
        auth.register(username='dbtest', email='dbtest@test.com')
        
        with sqlite3.connect('school_schedule.db') as conn:
            user = conn.execute(
                'SELECT username, email, role FROM users WHERE username = ?',
                ('dbtest',)
            ).fetchone()
            
            assert user is not None
            assert user[0] == 'dbtest'
            assert user[1] == 'dbtest@test.com'
            assert user[2] == 'student'

if __name__ == '__main__':
    pytest.main(['-v', __file__])
