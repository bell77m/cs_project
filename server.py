import socket
import threading
import bcrypt
import mysql.connector
import random
import string
import re
from datetime import datetime, timedelta


db = mysql.connector.connect(
    host="localhost",
    user="bell77m",
    password="237812341",
    database="chat_db"
)
cursor = db.cursor()

clients = []



def log_login(user_id, success):
    sql = "INSERT INTO login_logs (user_id, success) VALUES (%s, %s)"
    cursor.execute(sql, (user_id, success))
    db.commit()


def broadcast_message(message, sender_socket):
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                client_socket.send(message)
            except:
                client_socket.close()
                clients.remove(client_socket)


# Generate random token for password reset
def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))


# Validate password strength
def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[@$!%*?&]', password):
        return False, "Password must contain at least one special character."
    return True, "Password is strong."


# Function to handle clients
def handle_client(client_socket, addr):
    print(f"Connection established with {addr}")
    authenticated = False
    user_id = None
    username = None

    try:
        while True:
            if not authenticated:
                client_socket.send(
                    "Welcome! Choose an option: (1) Register (2) Login (3) Forget Password\n".encode('utf-8'))
                option = client_socket.recv(1024).decode('utf-8')

                if option == "1":  # Register
                    client_socket.send("Enter a username: ".encode('utf-8'))
                    username = client_socket.recv(1024).decode('utf-8')

                    client_socket.send("Enter a password: ".encode('utf-8'))
                    password = client_socket.recv(1024).decode('utf-8')

                    valid, msg = validate_password_strength(password)
                    if not valid:
                        client_socket.send(f"Error: {msg}\n".encode('utf-8'))
                        continue

                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cursor.fetchone():
                        client_socket.send("Username already taken. Try again.\n".encode('utf-8'))
                    else:
                        cursor.execute(
                            "INSERT INTO users (username, password_hash, last_password_change) VALUES (%s, %s, %s)",
                            (username, hashed_password, datetime.now()))
                        db.commit()
                        client_socket.send("Registration successful!\n".encode('utf-8'))

                elif option == "2":  # Login
                    client_socket.send("Username: ".encode('utf-8'))
                    username = client_socket.recv(1024).decode('utf-8')
                    client_socket.send("Password: ".encode('utf-8'))
                    password = client_socket.recv(1024).decode('utf-8')

                    cursor.execute(
                        "SELECT id, password_hash, last_password_change, failed_attempts, account_locked_until FROM users WHERE username = %s",
                        (username,))
                    user = cursor.fetchone()

                    if user:
                        user_id, password_hash, last_password_change, failed_attempts, account_locked_until = user

                        # account is locked
                        if account_locked_until and account_locked_until > datetime.now():
                            client_socket.send(
                                f"Account locked until {account_locked_until}. Try again later.\n".encode('utf-8'))
                            continue

                        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                            authenticated = True
                            log_login(user_id, True)
                            client_socket.send("Login successful!\n".encode('utf-8'))

                            # Reset failed attempts
                            cursor.execute("UPDATE users SET failed_attempts = 0 WHERE username = %s", (username,))
                            db.commit()

                            # password  changed
                            if (datetime.now() - last_password_change).days > 90:
                                client_socket.send("Your password has expired. Please change it.\n".encode('utf-8'))

                            # Add client
                            clients.append(client_socket)

                            # Notify others
                            broadcast_message(f"{username} has joined the chat.\n".encode('utf-8'), client_socket)
                        else:
                            failed_attempts += 1
                            if failed_attempts >= 5:
                                account_locked_until = datetime.now() + timedelta(minutes=15)
                                cursor.execute("UPDATE users SET account_locked_until = %s WHERE username = %s",
                                               (account_locked_until, username))
                            cursor.execute("UPDATE users SET failed_attempts = %s WHERE username = %s",
                                           (failed_attempts, username))
                            db.commit()

                            log_login(user_id, False)
                            client_socket.send("Invalid password!\n".encode('utf-8'))
                    else:
                        client_socket.send("User not found!\n".encode('utf-8'))

                elif option == "3":  # Forget Password
                    client_socket.send("Enter your username: ".encode('utf-8'))
                    username = client_socket.recv(1024).decode('utf-8')

                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    user = cursor.fetchone()

                    if user:
                        user_id = user[0]
                        reset_token = generate_reset_token()
                        reset_token_expire = datetime.now() + timedelta(hours=1)

                        cursor.execute("UPDATE users SET reset_token = %s, reset_token_expire = %s WHERE id = %s",
                                       (reset_token, reset_token_expire, user_id))
                        db.commit()

                        client_socket.send(f"Password reset token: {reset_token}\n".encode('utf-8'))
                        client_socket.send("Token expires in 1 hour.\n".encode('utf-8'))
                    else:
                        client_socket.send("User not found!\n".encode('utf-8'))

                else:
                    client_socket.send("Invalid option.\n".encode('utf-8'))

            else:
                msg = client_socket.recv(1024).decode('utf-8')
                if not msg:
                    break
                print(f"{username}: {msg}")
                broadcast_message(f"{username}: {msg}\n".encode('utf-8'), client_socket)
                client_socket.send("Message sent.\n".encode('utf-8'))

    except (ConnectionResetError, BrokenPipeError):
        print(f"Connection with {addr} was lost.")

    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        broadcast_message(f"{username} has left the chat.\n".encode('utf-8'), client_socket)
        client_socket.close()


# Start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5551))
    server_socket.listen(5)

    print("Server is listening...")

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()


if __name__ == "__main__":
    start_server()
