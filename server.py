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
        self.disconnected_callback = None

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
                self.disconnected_callback(client)
                self.connected -= 1
                print(f"[CONNECT] Disconnected [{self.connected}/{MAX_PLAYERS}]!")
                self.send_all(f'10_{self.connected}_{MAX_PLAYERS}')
                return


class Player:
    def __init__(self, client):
        self.client = client
        self.money = 150.0
        self.wood = 100
        self.id = -1


class ServerGame:
    def __init__(self, server):
        self.lock = Lock()
        self.all_sprites = Group()
        self.buildings = Group()
        self.players = {}
        self.server = server

    def add_player(self, client, id):
        self.lock.acquire()
        p = Player(client)
        p.id = id
        self.players[id] = p
        self.lock.release()

    def remove_player(self, client):
        self.lock.acquire()
        for i, j in self.players.items():
            if j.client == client:
                p = i
                break
        self.players.pop(p, None)
        self.lock.release()

    def update(self, *args):
        self.all_sprites.update(*args)

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
    pygame.mouse.set_visible(0)
    connect_info = [0, 0]

    def pre_read(cmd, args, client):
        print(cmd, args)
        if cmd == '10':  # Player is ready
            connect_info[1] += 1
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
        connect_info[0] += 1

    def disconnect_player(client):
        if client.ready:
            connect_info[1] -= 1
        connect_info[0] -= 1

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
    server.disconnected_callback = disconnect_player
    thread = threading.Thread(target=server.thread_connection, daemon=True)
    thread.start()
    font = pygame.font.Font(None, 50)
    background = pygame.image.load('sprite-games/play/Основа.png')
    pygame.mouse.set_visible(0)
    image = {"host": (330, 183),
             "connect": (330, 386),
             "back": (330, 784),
             "ready": (1311, 784),
             "cancel": (1311, 784)}

    class Button(pygame.sprite.Sprite):
        def __init__(self, group, name, image1=None):
            super().__init__(group)
            if image1:
                self.stok_image = pygame.image.load(f'sprite-games/play/anim/{name}.png')
            else:
                self.stok_image = pygame.image.load(f'sprite-games/play/{name}.png')
            self.anim = pygame.image.load(f'sprite-games/play/anim/{name}.png')
            self.name = name
            self.image = self.stok_image
            self.rect = self.image.get_rect()
            self.rect.topleft = image[name]

        def get_anim(self, event):
            if self.rect.collidepoint(event.pos):
                self.image = self.anim
            else:
                if self.image == self.anim:
                    self.image = self.stok_image

        def get_event(self, event):
            if self.rect.collidepoint(event.pos):
                if self.name == "back" or self.name == "cancel":
                    return True

    class Cursor(pygame.sprite.Sprite):
        def __init__(self, group):
            super().__init__(group)
            self.image = pygame.image.load('sprite-games/menu/cursor.png')
            self.rect = self.image.get_rect()

    all_buttons = pygame.sprite.Group()
    for n, i in enumerate(image):
        if n < 3:
            if n == 0:
                Button(all_buttons, i, 1)
            else:
                Button(all_buttons, i)
    cancel_buttons = pygame.sprite.Group()
    Button(cancel_buttons, "cancel")
    all_cursor = pygame.sprite.Group()
    cursor = Cursor(all_cursor)
    pygame.mouse.set_visible(0)
    while not server.is_ready():
        pygame.mouse.set_visible(0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in cancel_buttons:
                    a = button.get_event(event)
                    if a:
                        return
            if event.type == pygame.MOUSEMOTION:
                for button in cancel_buttons:
                    button.get_anim(event)
        pygame.mouse.set_visible(0)
        screen.blit(background, (0, 0))
        # Отрисовка информации!
        text = font.render(f'Сообщите ip остальным игрокам:', 1, (200, 200, 200))
        screen.blit(text, (650, 310)) #5
        text = font.render(f'[{server_ip}]', 1, (255, 5, 5))
        screen.blit(text, (650, 355))#50
        text = font.render(f'Подключено [{connect_info[0]}/{MAX_PLAYERS}]', 1, (200, 200, 200))
        screen.blit(text, (650, 405))#100
        text = font.render(f'Готово: [{connect_info[1]}]', 1, (200, 200, 200))
        screen.blit(text, (650, 455))#150
        all_buttons.draw(screen)
        cursor.rect.topleft = pygame.mouse.get_pos()
        cancel_buttons.draw(screen)
        all_cursor.draw(screen)
        pygame.display.flip()

    for i, c in enumerate(server.clients):
        game.add_player(c, i)
        c.send(f'0_{i}')

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
                for spr in game.all_sprites:
                    spr.send_updated(game)
                game.lock.release()
            elif event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return
        screen.fill((195, 195, 250))
        # Отрисовка информации!
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    pygame.init()
    main(pygame.display.set_mode((1000, 1000)))
    print('\n\tServer closed.\n')
