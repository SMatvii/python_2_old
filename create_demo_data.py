import sqlite3
import bcrypt
from datetime import datetime, timedelta

def create_demo_data():
    conn = sqlite3.connect('school_schedule.db')
    cursor = conn.cursor()
    
    demo_users = [
        ('admin', 'admin@school.com', 'admin123', 'admin'),
        ('teacher', 'teacher@school.com', 'teacher123', 'teacher'),
        ('student', 'student@school.com', 'student123', 'student'),
        ('ivan_petrov', 'ivan@school.com', 'password123', 'student'),
        ('maria_kovalenko', 'maria@school.com', 'password123', 'student'),
    ]
    
    print("Створення демо користувачів...")
    for username, email, password, role in demo_users:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, role)
            )
            print(f"✓ Створено користувача: {username} ({role})")
        except sqlite3.IntegrityError:
            print(f"⚠ Користувач {username} вже існує")
    
    demo_lessons = [
        ('Математика', 'Іванова О.П.', '201', 'Понеділок', '08:00', '09:35'),
        ('Українська мова', 'Петренко М.І.', '105', 'Понеділок', '09:50', '11:25'),
        ('Фізика', 'Сидоров В.А.', '301', 'Понеділок', '11:40', '13:15'),
        ('Англійська мова', 'Brown J.', '108', 'Понеділок', '14:00', '15:35'),
        
        ('Хімія', 'Ковальчук Н.В.', '302', 'Вівторок', '08:00', '09:35'),
        ('Історія', 'Мельник Т.С.', '203', 'Вівторок', '09:50', '11:25'),
        ('Географія', 'Шевченко А.М.', '204', 'Вівторок', '11:40', '13:15'),
        ('Фізкультура', 'Руденко С.О.', 'Спортзал', 'Вівторок', '14:00', '15:35'),
        
        ('Математика', 'Іванова О.П.', '201', 'Середа', '08:00', '09:35'),
        ('Біологія', 'Коваленко Л.П.', '303', 'Середа', '09:50', '11:25'),
        ('Інформатика', 'Тарасенко Д.В.', '401', 'Середа', '11:40', '13:15'),
        ('Мистецтво', 'Волкова К.О.', '110', 'Середа', '14:00', '15:35'),
        
        ('Українська література', 'Петренко М.І.', '105', 'Четвер', '08:00', '09:35'),
        ('Фізика', 'В.А.', '301', 'Четвер', '09:50', '11:25'),
        ('Англійська мова', 'Brown J.', '108', 'Четвер', '11:40', '13:15'),
        ('Хімія', 'Ковальчук Н.В.', '302', 'Четвер', '14:00', '15:35'),
        
        ('Математика', 'Іванова О.П.', '201', 'П\'ятниця', '08:00', '09:35'),
        ('Історія', 'Мельник Т.С.', '203', 'П\'ятниця', '09:50', '11:25'),
        ('Трудове навчання', 'Гриценко В.М.', '501', 'П\'ятниця', '11:40', '13:15'),
        ('Класна година', 'Петренко М.І.', '105', 'П\'ятниця', '14:00', '15:35'),
    ]
    
    print("\nСтворення демо розкладу...")
    for subject, teacher, classroom, day, time_start, time_end in demo_lessons:
        try:
            cursor.execute(
                'INSERT INTO lessons (subject, teacher, classroom, day_of_week, time_start, time_end, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (subject, teacher, classroom, day, time_start, time_end, 1)  # створено адміном
            )
            print(f"✓ Додано урок: {subject} ({day}, {time_start})")
        except sqlite3.IntegrityError:
            print(f"⚠ Урок {subject} в {day} о {time_start} вже існує")
    
    demo_tasks = [
        ('Розв\'язати рівняння 15-20', 'Сторінка 45, завдання 15-20', 'Математика', '2025-08-10'),
        ('Твір про літо', 'Написати твір на тему "Мої літні канікули" (200-300 слів)', 'Українська мова', '2025-08-12'),
        ('Лабораторна робота №3', 'Дослідження коливань математичного маятника', 'Фізика', '2025-08-15'),
        ('Презентація про країну', 'Підготувати презентацію про англомовну країну (10 слайдів)', 'Англійська мова', '2025-08-18'),
        ('Вивчити таблицю Менделєєва', 'Вивчити перші 20 елементів таблиці Менделєєва', 'Хімія', '2025-08-14'),
        ('Реферат про Другу світову війну', 'Написати реферат про причини і наслідки Другої світової війни', 'Історія', '2025-08-20'),
        ('Карта України', 'Позначити на контурній карті всі обласні центри України', 'Географія', '2025-08-16'),
        ('Програма "Калькулятор"', 'Написати програму калькулятора на Python', 'Інформатика', '2025-08-25'),
    ]
    
    print("\nСтворення демо завдань...")
    for title, description, subject, due_date in demo_tasks:
        try:
            cursor.execute(
                'INSERT INTO tasks (title, description, subject, due_date, user_id) VALUES (?, ?, ?, ?, ?)',
                (title, description, subject, due_date, 4)
            )
            print(f"✓ Додано завдання: {title}")
        except sqlite3.IntegrityError:
            print(f"⚠ Завдання {title} вже існує")

    demo_test_results = [
        (4, 'Загальний тест знань', 8, 10),
        (5, 'Загальний тест знань', 7, 10),
        (4, 'Тест з математики', 9, 10),
        (5, 'Тест з математики', 6, 10),
        (4, 'Тест з української мови', 10, 10),
    ]
    
    print("\nСтворення демо результатів тестів...")
    for user_id, test_name, score, total in demo_test_results:
        try:
            cursor.execute(
                'INSERT INTO test_results (user_id, test_name, score, total_questions) VALUES (?, ?, ?, ?)',
                (user_id, test_name, score, total)
            )
            print(f"✓ Додано результат тесту: {test_name} - {score}/{total}")
        except sqlite3.IntegrityError:
            print(f"⚠ Результат тесту вже існує")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Демо дані успішно створені!")
    print("\nДемо акаунти для входу:")
    print("├── Адміністратор: admin / admin123")
    print("├── Вчитель: teacher / teacher123")
    print("├── Учень: student / student123")
    print("├── Іван Петров: ivan_petrov / password123")
    print("└── Марія Коваленко: maria_kovalenko / password123")

if __name__ == '__main__':
    create_demo_data()
