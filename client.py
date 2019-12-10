import socket
import threading


class Client:
    def __init__(self, name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = 5556
        self.addr = (self.server, self.port)
        self.name = name
        self.i = 0
        self.connect()
        thread = threading.Thread(target=self.thread_listen)
        thread.start()

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.client.sendall(self.name.encode())
        except Exception as e:
            self.disconnect(e)

    def send(self, data):
        try:
            self.client.send(data.encode())
        except socket.error as e:
            self.disconnect(e)

    def disconnect(self, msg):
        print("[EXCEPTION] Disconnected from server:", msg)
        self.client.close()

    def thread_listen(self):
        while True:
            msg = self.client.recv(1024)
            print('taken command', msg)
            if msg.startswith('0'.encode()):
                self.i = self.i + 1
            elif msg.startswith('1'.encode()):
                print('I is:', self.i)


if __name__ == '__main__':
    n = Client(input())
    while True:
        n.send(input())
