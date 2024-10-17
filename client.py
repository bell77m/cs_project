import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(message)
            else:
                break
        except:
            print("Connection lost.")
            client_socket.close()
            break

def chat_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5551))


    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    while True:

        message = input()
        if message:
            client.send(message.encode('utf-8'))

if __name__ == "__main__":
    chat_client()
