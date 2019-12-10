import socket
import threading


class ClienConnection:
    def __init__(self, addr, name, conn):
        self.addr, self.name, self.conn = addr, name, conn

    def send(self, msg):
        print(msg)
        self.conn.send(msg.encode())


class Server:
    def __init__(self):
        self.clients = []

    def send_all(self, msg):
        for c in self.clients:
            print(c)
            c.send(msg)

    def thread_connection(self):
        server = "localhost"
        port = 5556
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((server, port))
        except socket.error as e:
            print(str(e))

        s.listen(1)
        print("Waiting for a connection, Server Started")

        while True:
            print("[CONNECT] Finding connection!")
            conn, addr = s.accept()
            print("[CONNECT] New connection!")

            self.authentication(conn, addr)

    def authentication(self, conn, addr):
        try:
            data = conn.recv(1024)
            name = str(data.decode())
            if not name:
                raise Exception("No name received")

            client = ClienConnection(addr, name, conn)
            self.clients.append(client)
            thread = threading.Thread(target=self.player_input_thread, args=(client, ))
            thread.start()
        except Exception as e:
            print("[EXCEPTION]", e)
            conn.close()

    def player_input_thread(self, client):
        while True:
            try:
                print('Server taken:', client.conn.recv(1024))
            except Exception as ex:
                print('[ERROR]', ex)


if __name__ == '__main__':
    server = Server()
    thread = threading.Thread(target=server.thread_connection)
    thread.start()
    # thread.join()
    while len(server.clients) == 0:
        pass
    server.send_all('0')
    server.send_all('0')
    server.send_all('1')
    print('Incremented.')
