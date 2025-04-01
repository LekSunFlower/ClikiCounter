import threading
import time
from datetime import datetime
import os

# Класс для хранения данных пользователя
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.key_presses = 0
        self.mouse_clicks = 0
        self.session_time = 0

# Глобальные переменные
users = {}
current_user = None
running = True
data_lock = threading.Lock()

# Загрузка данных пользователей из файла
def load_users():
    global users
    try:
        with open("users.txt", "r") as f:
            for line in f:
                username, password, key_presses, mouse_clicks = line.strip().split(":")
                users[username] = User(username, password)
                users[username].key_presses = int(key_presses)
                users[username].mouse_clicks = int(mouse_clicks)
    except FileNotFoundError:
        pass

# Сохранение данных пользователей в файл
def save_users():
    while running:
        with data_lock:
            with open("users.txt", "w") as f:
                for user in users.values():
                    f.write(f"{user.username}:{user.password}:{user.key_presses}:{user.mouse_clicks}\n")
        time.sleep(5)  # Сохранение каждые 5 секунд

# Логирование действий
def log_action(username, action):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open("program.log", "a") as f:
        f.write(f"[INFO] [{timestamp}] [{username}] - {action}\n")

def log_error(username, location, error):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open("program.log", "a") as f:
        f.write(f"[ERROR] [{timestamp}] [{username}] - {location}: {error}\n")

# Регистрация пользователя
def register():
    username = input("Введите имя пользователя: ")
    if username in users:
        print("Пользователь уже существует!")
        log_action(username, "Попытка регистрации существующего пользователя")
        return False
    password = input("Введите пароль: ")
    users[username] = User(username, password)
    log_action(username, "Успешная регистрация")
    return True

# Авторизация пользователя
def login():
    global current_user
    username = input("Введите имя пользователя: ")
    if username not in users:
        print("Пользователь не найден!")
        log_action(username, "Попытка входа с несуществующим пользователем")
        return False
    password = input("Введите пароль: ")
    if users[username].password == password:
        current_user = users[username]
        log_action(username, "Успешный вход")
        return True
    else:
        print("Неверный пароль!")
        log_action(username, "Попытка входа с неверным паролем")
        return False

# Отслеживание времени сессии
def session_timer():
    global running, current_user
    while running and current_user:
        current_user.session_time += 1
        if current_user.session_time >= 30:  # Лимит 30 секунд
            print("\nВремя сессии истекло! Выход из программы.")
            log_action(current_user.username, "Истекло время сессии")
            running = False
        time.sleep(1)

# Отслеживание ввода (кроссплатформенный вариант)
def input_counter():
    global running, current_user
    while running and current_user:
        try:
            print("\nВведите символ (m - клик мыши): ")
            char = input().strip()
            with data_lock:
                if char == "m":
                    current_user.mouse_clicks += 1
                    log_action(current_user.username, "Клик мыши")
                else:
                    current_user.key_presses += 1
                    log_action(current_user.username, "Нажатие клавиши")
        except EOFError:
            log_error(current_user.username, "input_counter", "Неожиданный конец ввода")
        time.sleep(0.1)

# Основной цикл программы
def main():
    global running, current_user
    load_users()

    # Запуск фонового потока для сохранения данных
    save_thread = threading.Thread(target=save_users, daemon=True)
    save_thread.start()

    while True:
        print("\n1. Регистрация\n2. Вход\n3. Выход")
        choice = input("Выберите действие: ")

        try:
            if choice == "1":
                register()
            elif choice == "2":
                if login():
                    # Запуск потоков для авторизованного пользователя
                    timer_thread = threading.Thread(target=session_timer, daemon=True)
                    counter_thread = threading.Thread(target=input_counter, daemon=True)
                    timer_thread.start()
                    counter_thread.start()

                    while running and current_user:
                        with data_lock:
                            print(f"\nНажатий клавиш: {current_user.key_presses}")
                            print(f"Кликов мыши: {current_user.mouse_clicks}")
                            print(f"Время сессии: {current_user.session_time} сек")
                        time.sleep(1)

                    running = True  # Сброс для следующего входа
                    current_user = None
            elif choice == "3":
                running = False
                log_action("SYSTEM", "Программа завершена")
                break
            else:
                print("Неверный выбор!")
        except Exception as e:
            # Используем None, если current_user еще не определен
            username = "SYSTEM" if current_user is None else current_user.username
            log_error(username, "Main loop", str(e))

if __name__ == "__main__":
    main()