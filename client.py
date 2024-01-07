import socket
import pickle
import sys, time, os
from PyQt6.QtCore import QThreadPool, QThread, pyqtSignal, QRunnable, pyqtSlot
from PyQt6.QtWidgets import QApplication
from client_gui import MainWindow, Video, Audio
from communication import *

# Server IP and port
SERVER_IP = '100.104.43.52'
MAIN_PORT = 8765
VIDEO_PORT = MAIN_PORT + 1
AUDIO_PORT = MAIN_PORT + 2
DISCONNECT_MSG = 'disconnect'
class Client:
    def __init__(self, name, addr=None):
        self.name = name
        self.addr = addr
        self.video = Video() if self.addr is None else None
        self.audio = Audio() if self.addr is None else None

    def get_video(self):
        return self.video.get_frame() if self.video is not None else None
    
    def get_audio(self):
        return self.audio.get_stream() if self.audio is not None else None

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

class ServerConnection(QThread):
    add_client_signal = pyqtSignal(Client)
    remove_client_signal = pyqtSignal(str)
    add_msg_signal = pyqtSignal(Message)

    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def run(self):
        while client.name == 'You':
            pass

        self.init_connection()
        self.start_conn_threads()
        self.start_broadcast_threads()
        self.add_client_signal.emit(client)

        while self.connected:
            pass
    
    def init_connection(self):
        self.main_socket.connect((SERVER_IP, MAIN_PORT))
        self.video_socket.connect((SERVER_IP, VIDEO_PORT))
        self.audio_socket.connect((SERVER_IP, AUDIO_PORT))
        self.connected = True
        self.main_socket.send(pickle.dumps(Message(client.name, 'add', 'main')))

    def start_conn_threads(self):
        self.main_thread = Worker(self.handle_main, self.main_socket)
        self.threadpool.start(self.main_thread)
        self.video_thread = Worker(self.handle_media, self.video_socket, 'video')
        self.threadpool.start(self.video_thread)
        self.audio_thread = Worker(self.handle_media, self.audio_socket, 'audio')
        self.threadpool.start(self.audio_thread)

    def start_broadcast_threads(self):
        self.video_broadcast_thread = Worker(self.broadcast_media, self.video_socket, 'video')
        self.threadpool.start(self.video_broadcast_thread)
        self.audio_broadcast_thread = Worker(self.broadcast_media, self.audio_socket, 'audio')
        self.threadpool.start(self.audio_broadcast_thread)
    
    def disconnect_all(self):
        msg = Message(client.name, DISCONNECT_MSG)
        self.main_socket.send(pickle.dumps(msg))
        self.main_socket.close()
        self.video_socket.close()
        self.audio_socket.close()

    def handle_main(self, conn):
        global all_clients, active_clients
        while self.connected:
            msg_bytes = conn.recv(4096)
            if not msg_bytes:
                self.connected = False
                break
            msg = pickle.loads(msg_bytes)
            # Process msg as per your logic

    def handle_media(self, conn, media):
        while self.connected:
            try:
                # Receive the size of the incoming message first
                size_data = conn.recv(4)
                if not size_data:
                    break

                # Convert the size to an integer
                msg_size = int.from_bytes(size_data, byteorder='big')

                # Now receive the actual message based on the received size
                msg_bytes = conn.recv(msg_size)
                if not msg_bytes:
                    break

                # Deserialize the message
                msg = pickle.loads(msg_bytes)

                # Process the message (depending on your application's logic)
                if msg.request == 'post':
                    if media == 'video':
                        # Handle video data
                        # For example, update the client's video frame
                        all_clients[msg.from_name].video_frame = msg.data
                    elif media == 'audio':
                        # Handle audio data
                        # For example, update the client's audio stream
                        all_clients[msg.from_name].audio_stream = msg.data
            except Exception as e:
                print(f"Error in handle_media: {e}")
                break


    def broadcast_media(self, conn, media):
        while self.connected:
            data = client.get_video() if media == 'video' else client.get_audio()
            if data is not None:
                msg = Message(client.name, 'post', media, data)
                conn.send(pickle.dumps(msg))

client = Client('You')
all_clients = {}

def main():
    app = QApplication(sys.argv)
    server = ServerConnection()
    window = MainWindow(client, server)
    window.show()
    app.exec()
    server.disconnect_all()
    os._exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n> Disconnecting...")
        exit(0)
