import pickle
import socket
import threading
from copy import deepcopy
from threading import Lock

import pygame
from pygame import sprite
from pygame.sprite import Group, Sprite
from constants import SERVER_EVENT_SEC, SERVER_EVENT_UPDATE, SERVER_EVENT_SYNC

from units import get_class_id, UNIT_TYPES, TARGET_MOVE

NEED_PLAYERS = 1
MAX_PLAYERS = 10

CURRENT_ID = 0
ID_LOCK = Lock()


def get_curr_id():
    global CURRENT_ID
    ID_LOCK.acquire()
    c = CURRENT_ID
    CURRENT_ID += 1
    ID_LOCK.release()
    return c


class ClientConnection:
    curr_id = 0

    def __init__(self, addr, conn):
        self.addr, self.conn = addr, conn
        self.id = ClientConnection.curr_id
        self.ready = False
        ClientConnection.curr_id += 1
        self.connected = True

    def send(self, msg):
        if self.connected:
            try:
                self.conn.send((msg + ';').encode())
            except Exception as ex:
                print('[ClientConnection::send]', ex)
                self.connected = False

    def send_bytes(self, msg):
        if self.connected:
            try:
                self.conn.send(msg + b';')
            except Exception as ex:
                print('[ClientConnection::send]', ex)
                self.connected = False


class Server:
    def __init__(self, ip='localhost'):
        self.ip = ip
        self.clients = []
        self.connected = 0
        self.waiting = True
        self.callback = None
        self.connected_callback = None

    def send_all(self, msg):
        for c in self.clients:
            c.send(msg)

    def send_others(self, client, msg):
        for c in self.clients:
            if c != client:
                c.send(msg)

    def is_ready(self):
        if not self.waiting:
            return True
        if len(self.clients) <= 0:
            return False
        for i in self.clients:
            if not i.ready:
                return False
        return True

    def thread_connection(self):
        server = self.ip
        port = 5556
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((server, port))
        except socket.error as e:
            print(str(e))

        s.listen(1)
        print("Waiting for a connection, Server Started")

        while self.connected < MAX_PLAYERS:
            print("[CONNECT] Finding connection!")
            conn, addr = s.accept()
            if self.is_ready():
                break
            self.connected += 1
            print(f"[CONNECT] Connected [{self.connected}/{MAX_PLAYERS}]!")
            self.authentication(conn, addr)
            self.send_all(f'10_{self.connected}_{MAX_PLAYERS}')
        self.waiting = False
        print('Everybody connected.')

    def authentication(self, conn, addr):
        try:
            client = ClientConnection(addr, conn)
            self.clients.append(client)
            self.connected_callback(client)
            thread = threading.Thread(target=self.player_input_thread, args=(client,), daemon=True)
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
                print(f"[CONNECT] Disconnected [{self.connected}/{MAX_PLAYERS}]!")
                self.send_all(f'10_{self.connected}_{MAX_PLAYERS}')
                return


class Player:
    def __init__(self, client):
        self.client = client
        self.money = 150.0
        self.id = self.client.id


class ServerGame:
    def __init__(self, server):
        self.lock = Lock()
        self.all_sprites = Group()
        self.buildings = Group()
        self.players = {}
        self.server = server

    def add_player(self, client):
        p = Player(client)
        self.lock.acquire()
        self.players[p.id] = p
        self.lock.release()

    def update(self, *args):
        self.lock.acquire()
        self.all_sprites.update(*args)
        self.lock.release()

    def place(self, build_class, x, y, player_id):
        self.lock.acquire()
        player = self.players[player_id]
        if player.money >= build_class.cost:
            building = build_class(x, y, get_curr_id(), player_id)
            if not sprite.spritecollideany(building, self.all_sprites):
                player.money -= build_class.cost
                self.server.send_all(
                    f'1_{get_class_id(build_class)}_{x}_{y}_{building.id}_{player_id}{building.get_args()}')
                self.all_sprites.add(building)
                if building.is_building:
                    self.buildings.add(building)
                player.client.send(f'3_1_{player.money}')
                print(f'Success {player.money}')
            else:
                print(f'No place {player.money}')
        else:
            print(f'No money {player.money}/{build_class.cost}')
        self.lock.release()

    def create_entity(self, clazz, x, y, player_id, *args):
        self.lock.acquire()
        print(x, y)
        building = clazz(x, y, get_curr_id(), player_id, *args)
        self.server.send_all(
            f'1_{get_class_id(clazz)}_{str(x)}_{str(y)}_{building.id}_{player_id}{building.get_args()}')
        self.all_sprites.add(building)
        self.lock.release()

    def get_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.all_sprites, False)

    def get_building_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.buildings, False)

    def retarget(self, id, x, y, client):
        for i in self.all_sprites:
            if i.id == id:
                if i.has_target:
                    self.lock.acquire()
                    if i.player_id == client.id:
                        i.set_target(TARGET_MOVE, (x, y))
                    self.lock.release()
                    return True
        return False

    def find_with_id(self, id):
        for spr in self.all_sprites:
            if spr.id == id:
                return spr

    def kill(self, spr):
        self.server.send_all(f'4_{spr.id}')
        spr.kill()


def place_on_map():
    pass


def main(screen):
    def pre_read(cmd, args, client):
        print(cmd, args)
        if cmd == '10':  # Player is ready
            print(client, 'ready')
            client.ready = True

    def read(cmd, args, client):
        print(cmd, args)
        if cmd == '1':
            game.place(UNIT_TYPES[int(args[0])], int(args[1]), int(args[2]), client.id)
        elif cmd == '2':
            id, x, y = list(map(int, args))
            print('Retarget:', id, x, y)
            if game.retarget(id, x, y, client):
                server.send_all(f'2_{TARGET_MOVE}_{id}_{x}_{y}')
            else:
                print(f'Entity[{id}] has not got a "target"')
        else:
            print('Invalid command')

    def connect_player(client):
        game.add_player(client)

    def update_players_info():
        for pl in game.players.values():
            pl.client.send(f'3_1_{pl.money}')

    with open('server_setting.txt') as settings:
        server_ip = settings.readline()
        if server_ip == 'auto':
            server_ip = socket.gethostbyname(socket.gethostname())
    print('\n\tYour ip is:', server_ip, '\n')
    pygame.mouse.set_visible(True)
    server = Server(server_ip)
    game = ServerGame(server)
    server.callback = pre_read
    server.connected_callback = connect_player
    thread = threading.Thread(target=server.thread_connection, daemon=True)
    thread.start()
    font = pygame.font.Font(None, 50)

    while not server.is_ready():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return
        screen.fill((50, 150, 255))

        # Отрисовка информации!
        text_top = font.render(f'Сообщите ip остальным игрокам:', 1, (200, 200, 200))
        text_bottom = font.render(f'[{server_ip}]', 1, (255, 5, 5))
        screen.blit(text_top, (5, 5))
        screen.blit(text_bottom, (5, 50))

        pygame.display.flip()

    for c in server.clients:
        c.send(f'0_{c.id}')

    clock = pygame.time.Clock()

    server.callback = read
    running = True
    pygame.time.set_timer(SERVER_EVENT_UPDATE, 1000 // 60)
    pygame.time.set_timer(SERVER_EVENT_SEC, 1000 // 1)
    pygame.time.set_timer(SERVER_EVENT_SYNC, 10000)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in [SERVER_EVENT_UPDATE, SERVER_EVENT_SEC]:
                game.update(event, game)
                if event.type == SERVER_EVENT_SEC:
                    update_players_info()
            elif event.type == SERVER_EVENT_SYNC:
                game.lock.acquire()
                print('Sync')
                game.lock.release()
        clock.tick(60)


if __name__ == '__main__':
    pygame.init()
    main(pygame.display.set_mode((500, 500)))
    print('Server closed.')
