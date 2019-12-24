import socket
import threading

NEED_PLAYERS = 3


class ClienConnection:
    curr_id = 0

    def __init__(self, addr, conn):
        self.addr, self.conn = addr, conn
        self.id = ClienConnection.curr_id
        ClienConnection.curr_id += 1

    def send(self, msg):
        self.conn.send(msg.encode())


class Server:
    def __init__(self):
        self.clients = []
        self.connected = 0
        self.waiting = True

    def send_all(self, msg):
        for c in self.clients:
            c.send(msg)

    def send_others(self, client, msg):
        for c in self.clients:
            if c != client:
                c.send(msg)

    def thread_connection(self, ip='localhost'):
        server = ip
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
        print('Everybody connected.')
        self.waiting = False

    def authentication(self, conn, addr):
        try:
            client = ClienConnection(addr, conn)
            self.clients.append(client)
            thread = threading.Thread(target=self.player_input_thread, args=(client, ))
            client.thread = thread
            thread.start()
            print(f"[AUTHENTICATION] Thread for client '{client.id}' started.")
        except Exception as e:
            print("[AUTHENTICATION][ERROR]", e)
            conn.close()

    def player_input_thread(self, client):
        while True:
            try:
                command = client.conn.recv(1024).decode()

                # 0 - Send cmd to other clients
                if command.startswith('0'):
                    print('Command 0.', command)
                    self.send_others(client, command[2::])
                else:
                    print('Invalid command:', command)
            except Exception as ex:
                print('[PLAYER THREAD ERROR] from client:', client.id, ex)
                self.clients.remove(client)
                if self.waiting:
                    self.connected -= 1
                    print(f"[CONNECT] Disconnected [{self.connected}/{NEED_PLAYERS}]!")
                return


def main():
    server = Server()
    thread = threading.Thread(target=server.thread_connection)
    thread.start()
    thread.join()


if __name__ == '__main__':
    main()
    print('Server closed.')
