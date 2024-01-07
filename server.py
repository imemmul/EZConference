import socket
import threading
import time
import os
import pickle
from dataclasses import dataclass, field
from communication import *

# Server IP and port
IP = '100.104.43.52'
MAIN_PORT = 8765
VIDEO_PORT = MAIN_PORT + 1
AUDIO_PORT = MAIN_PORT + 2

VIDEO = 'video'
AUDIO = 'audio'
ADD = 'add'
RM = 'rm'
DISCONNECT_MSG = 'disconnect'

clients = {}  # list of clients connected to the server

@dataclass
class Client:
    name: str
    main_conn: socket.socket
    addr: str
    connected: bool
    media_conn: socket.socket = None

def disconnect_client(client: Client):
    global clients
    print(f"[DISCONNECTING] {client.name} disconnected from Main Server")
    client.connected = False
    client.main_conn.close()
    if client.media_conn:
        client.media_conn.close()
    clients.pop(client.name)

def handle_client(name: str):
    client = clients[name]
    conn = client.main_conn

    # Add all clients to current client
    for client_name in clients:
        msg = Message(client_name, ADD)
        if client_name != name:
            conn.send(pickle.dumps(msg))
    
    # Add current client to all clients
    msg = Message(name, ADD)
    for client_name in clients:
        if client_name != name:
            client_conn = clients[client_name].main_conn
            client_conn.send(pickle.dumps(msg))

    while client.connected:
        try:
            msg_bytes = conn.recv(4096)
            if not msg_bytes:
                break
            msg = pickle.loads(msg_bytes)
            if msg.request == DISCONNECT_MSG:
                break
            for name in msg.to_names:
                if name not in clients:
                    continue
                client_conn = clients[name].main_conn
                client_conn.send(pickle.dumps(msg))
        except Exception as e:
            print(f"Error: {e}")
            break
    
    disconnect_client(client)

def media_server(media: str):
    if media == VIDEO:
        PORT = VIDEO_PORT
    elif media == AUDIO:
        PORT = AUDIO_PORT

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()

    print(f"[LISTENING] {media} Server is listening on {IP}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_media_client, args=(conn, addr, media)).start()

def handle_media_client(conn, addr, media):
    name = None
    try:
        while True:
            msg_bytes = conn.recv(4096)
            if not msg_bytes:
                break
            msg = pickle.loads(msg_bytes)
            name = msg.from_name

            if msg.request == ADD:
                clients[name].media_conn = conn
                print(f"[CONNECTING] {name} connected to {media} Server")
            else:
                # Forward the message to other clients
                for client_name, client in clients.items():
                    if client_name != name and client.media_conn:
                        client.media_conn.send(msg_bytes)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if name:
            clients[name].media_conn = None

def main():
    global clients
    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    main_socket.bind((IP, MAIN_PORT))
    main_socket.listen()
    print(f"[LISTENING] Main Server is listening on {IP}:{MAIN_PORT}")

    threading.Thread(target=media_server, args=(VIDEO,)).start()
    threading.Thread(target=media_server, args=(AUDIO,)).start()

    while True:
        conn, addr = main_socket.accept()
        try:
            name = conn.recv(4096).decode()
            clients[name] = Client(name, conn, addr, True)
            print(f"[NEW CONNECTION] {name} connected to Main Server")
            threading.Thread(target=handle_client, args=(name,)).start()
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"[EXITING] Keyboard Interrupt")
        for client in clients.values():
            disconnect_client(client)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        os._exit(0)
