import socket
import threading

NEED_PLAYERS = 3


class ClienConnection:
    def __init__(self, addr, name, conn):
        self.addr, self.name, self.conn = addr, name, conn

    def send(self, msg):
        print(msg)
        self.conn.send(msg.encode())


class Server:
    def __init__(self):
        self.clients = []
        self.connected = 0
        self.waiting = True

    def send_all(self, msg):
        for c in self.clients:
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

        while self.connected < NEED_PLAYERS:
            print("[CONNECT] Finding connection!")
            conn, addr = s.accept()
            self.connected += 1
            print(f"[CONNECT] Connected [{self.connected}/{NEED_PLAYERS}]!")
            self.authentication(conn, addr)
        self.send_all('0')
        self.waiting = False

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
            print(f"[AUTHENTICATION] Thread for client '{client.name}' started.")
        except Exception as e:
            print("[AUTHENTICATION][ERROR]", e)
            conn.close()

    def player_input_thread(self, client):
        while True:
            try:
                command = client.conn.recv(1024).decode()
                # 0 - Send cmd to other clients
                if command.startswith('0'):
                    print('Command 0.')
                    for cl in self.clients:
                        if client != cl:
                            cl.send(command[2::])
                else:
                    print('Invalid command:', command)
            except Exception as ex:
                print('[PLAYER THREAD ERROR] from:', client.name, ex)
                self.clients.remove(client)
                if self.waiting:
                    self.connected -= 1
                    print(f"[CONNECT] Disconnected [{self.connected}/{NEED_PLAYERS}]!")
                return


if __name__ == '__main__':
    server = Server()
    thread = threading.Thread(target=server.thread_connection)
    thread.start()
    thread.join()
    print('Server closed.')
