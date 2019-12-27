import socket
import threading
from threading import Lock

import pygame

NEED_PLAYERS = 1


class ClienConnection:
    curr_id = 0

    def __init__(self, addr, conn):
        self.addr, self.conn = addr, conn
        self.id = ClienConnection.curr_id
        ClienConnection.curr_id += 1

    def send(self, msg):
        self.conn.send((msg + ';').encode())


class Server:
    def __init__(self):
        self.clients = []
        self.connected = 0
        self.waiting = True
        self.callback = None

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
            self.send_all(f'10_{self.connected}_{NEED_PLAYERS}')
        self.send_all('0')
        print('Everybody connected.')
        self.waiting = False

    def authentication(self, conn, addr):
        try:
            client = ClienConnection(addr, conn)
            self.clients.append(client)
            thread = threading.Thread(target=self.player_input_thread, args=(client,))
            client.thread = thread
            thread.start()
            print(f"[AUTHENTICATION] Thread for client '{client.id}' started.")
        except Exception as e:
            print("[AUTHENTICATION][ERROR]", e)
            conn.close()

    def player_input_thread(self, client):
        command_buffer = ''
        while True:
            try:
                command_buffer += client.conn.recv(1024).decode()
                splitter = command_buffer.find(';')
                while splitter != -1:
                    command = command_buffer[:splitter]
                    if command != '':
                        command = command.split('_')
                        cmd, *args = command
                        self.callback(cmd, args, client)
                    command_buffer = command_buffer[splitter + 1:]
                    splitter = command_buffer.find(';')
            except Exception as ex:
                print('[PLAYER THREAD ERROR] from client:', client.id, ex)
                self.clients.remove(client)
                self.connected -= 1
                print(f"[CONNECT] Disconnected [{self.connected}/{NEED_PLAYERS}]!")
                self.send_all(f'10_{self.connected}_{NEED_PLAYERS}')
                return


class Bomb(pygame.sprite.Sprite):
    bomb = pygame.image.load('sprites/bomb.png')

    def __init__(self, group, x, y, id):
        self.rect = self.bomb.get_rect()
        self.rect.x = x
        self.rect.y = y
        super().__init__(group)


curr_id, id_lock = 0, Lock()


def main():
    def read(cmd, args, client):
        global curr_id
        print(cmd, args)
        if cmd == '1':  # Add object at [x, y]
            id_lock.acquire()
            x, y = list(map(int, args))
            # game.addSprite(x, y)
            server.send_all(f'1_{x}_{y}_{curr_id}')
            # print(curr_id)
            curr_id += 1
            id_lock.release()
        elif cmd == '2':  # Retarget
            id_lock.acquire()
            id, x, y = list(map(int, args))
            print('Retarget:', id, x, y)
            server.send_all(f'2_{id}_{x}_{y}')
            id_lock.release()
        else:
            print('Invalid command')

    # group = pygame.sprite.Group()

    server = Server()
    server.callback = read
    thread = threading.Thread(target=server.thread_connection)
    thread.start()
    thread.join()


if __name__ == '__main__':
    main()
    print('Server closed.')
