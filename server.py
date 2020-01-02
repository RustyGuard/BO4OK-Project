import math
import socket
import threading
from random import randint
from threading import Lock

import pygame
from pygame import sprite
from pygame.sprite import Group, Sprite

# Constants
NEED_PLAYERS = 1
EVENT_UPDATE = 30
EVENT_SEC = 31
CURRENT_ID = 0
ID_LOCK = Lock()


def get_curr_id():
    global CURRENT_ID
    ID_LOCK.acquire()
    c = CURRENT_ID
    CURRENT_ID += 1
    ID_LOCK.release()
    return c


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
        self.connected_callback = None

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
        self.waiting = False
        print('Everybody connected.')

    def authentication(self, conn, addr):
        try:
            client = ClienConnection(addr, conn)
            self.clients.append(client)
            self.connected_callback(client)
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


class Unit(Sprite):

    def __init__(self, x, y, player_id, *groups):
        global CURRENT_ID
        self.rect = self.image.get_rect()  # Init image before __init__
        self.x = float(x)
        self.y = float(y)
        self.rect.centerx = x
        self.rect.centery = y
        self.id = get_curr_id()
        self.player_id = player_id
        self.has_target = False
        super().__init__(*groups)

    def move(self, x, y):
        self.x += x
        self.rect.centerx = int(self.x)
        self.y += y
        self.rect.centery = int(self.y)

    def get_args(self):
        return ''


class Mine(Unit):
    cost = 100.0
    mine = pygame.image.load('sprites/mine.png')

    def __init__(self, x, y, player_id, *groups):
        self.image = Mine.mine
        super().__init__(x, y, player_id, *groups)

    def update(self, *args):
        if args:
            if args[0].type == EVENT_SEC:
                args[1].players[self.player_id].money += 5


class Bomb(Unit):
    cost = 10.0
    bomb = pygame.image.load('sprites/bomb.png')

    def __init__(self, x, y, player_id, *groups):
        self.angle = 0
        self.image = Bomb.bomb
        self.target = None
        self.target_angle = 0
        # self.set_angle(random.randint(0, 359))

        super().__init__(x, y, player_id, *groups)
        self.has_target = True

    def set_angle(self, angle):
        self.angle = angle
        self.validate_angle()
        self.update_image()

    def add_angle(self, angle):
        self.angle += angle
        self.validate_angle()
        self.update_image()

    def validate_angle(self):
        while self.angle >= 360:
            self.angle -= 360
        while self.angle < 0:
            self.angle += 360

    def update_image(self):
        center = Bomb.bomb.get_rect().center
        rotated_image = pygame.transform.rotate(Bomb.bomb, -self.angle)
        new_rect = rotated_image.get_rect(center=center)
        new_rect.centerx = self.rect.centerx
        new_rect.centery = self.rect.centery
        self.image = rotated_image
        self.rect = new_rect

    def move(self, x, y):
        self.x += x
        self.rect.centerx = int(self.x)
        self.y += y
        self.rect.centery = int(self.y)

    def update(self, *args):
        if args:
            if args[0].type == EVENT_UPDATE:
                if self.target is not None:
                    xr = self.target[0] - self.rect.centerx
                    yr = self.target[1] - self.rect.centery
                    if math.sqrt(xr * xr + yr * yr) < 50:
                        self.target = None
                        return
                    self.set_angle(int(math.degrees(math.atan2(yr, xr))))
                    self.move(math.cos(math.radians(self.angle)) * 0.5, math.sin(math.radians(self.angle)) * 0.5)


class Player:
    def __init__(self, client):
        self.client = client
        self.money = 150.0
        self.id = self.client.id
        self.color = (randint(0, 255), randint(0, 255), randint(0, 255))


class ServerGame:
    def __init__(self, server):
        self.lock = Lock()
        self.all_sprites = Group()
        self.projectiles = Group()
        self.players = {}
        self.server = server
        self.types = {
            0: Bomb,
            1: Mine
        }

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
            building = build_class(x, y, player_id)
            if not sprite.spritecollideany(building, self.all_sprites):
                player.money -= build_class.cost
                self.all_sprites.add(building)
                self.server.send_all(f'1_{self.get_type_id(build_class)}_{x}_{y}_{building.id}_{player_id}{building.get_args()}')
                player.client.send(f'3_1_{player.money}')
                print(f'Success {player.money}')
            else:
                print(f'No place {player.money}')
        else:
            print(f'No money {player.money}/{build_class.cost}')
        self.lock.release()

    def retarget(self, id, x, y):
        for i in self.all_sprites:
            if i.id == id:
                if i.has_target:
                    self.lock.acquire()
                    i.target = (x, y)
                    self.lock.release()
                    return True
        return False

    def get_type_id(self, type):
        for i, j in self.types.items():
            if j == type:
                return i


def main():

    def read(cmd, args, client):
        print(cmd, args)
        if cmd == '1':
            game.place(game.types[int(args[0])], int(args[1]), int(args[2]), client.id)
        elif cmd == '2':
            id, x, y = list(map(int, args))
            print('Retarget:', id, x, y)
            if game.retarget(id, x, y):
                server.send_all(f'2_{id}_{x}_{y}')
            else:
                print(f'Entity[{id}] has not got a "target"')
        else:
            print('Invalid command')

    def connect_player(client):
        game.add_player(client)

    server = Server()
    game = ServerGame(server)
    server.callback = read
    server.connected_callback = connect_player
    thread = threading.Thread(target=server.thread_connection)
    thread.start()
    thread.join()

    pygame.init()
    running = True
    clock = pygame.time.Clock()
    pygame.time.set_timer(EVENT_UPDATE, 1000 // 60)
    pygame.time.set_timer(EVENT_SEC, 1000 // 1)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type in [EVENT_UPDATE, EVENT_SEC]:
                game.update(event, game)
                if event.type == EVENT_SEC:
                    for pl in game.players.values():
                        pl.client.send(f'3_1_{pl.money}')
        clock.tick(60)


if __name__ == '__main__':
    main()
    print('Server closed.')
