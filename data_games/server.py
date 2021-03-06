import logging
import socket
import threading
from math import radians, cos, sin
from random import choice
from threading import Lock
from typing import Tuple, Dict

from pygame import sprite
from pygame.sprite import Group

from . import data
from .units import *

NEED_PLAYERS = 2
MAX_PLAYERS = 10

CURRENT_ID = 0
FREE_ID = []
ID_LOCK = Lock()

settings = {}


def get_curr_id():
    global CURRENT_ID
    ID_LOCK.acquire()
    if FREE_ID:
        ret = FREE_ID.pop(0)
        logging.info('Free id taken', ret)
        ID_LOCK.release()
        return ret
    c = CURRENT_ID
    CURRENT_ID += 1
    logging.debug('Current id is %d', CURRENT_ID)
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
        self.nick = None

    def disconnect(self, msg):
        logging.info('Disconnected %s', msg)
        self.conn.close()

    def send(self, msg):
        if self.connected:
            try:
                self.conn.send((msg + ';').encode())
            except Exception as ex:
                logging.info('[ClientConnection::send] %s', ex)
                self.connected = False

    def send_bytes(self, msg):
        if self.connected:
            try:
                self.conn.send(msg + b';')
            except Exception as ex:
                logging.info('[ClientConnection::send] %s', ex)
                self.connected = False


class Server:
    def __init__(self, ip='localhost'):
        self.ip = ip
        self.clients = []
        self.connected = True
        self.players = 0
        self.waiting = True
        self.callback = None
        self.connected_callback = None
        self.disconnected_callback = None

    def send_all(self, msg):
        for c in self.clients:
            c.send(msg)

    def disconnect(self):
        self.connected = False
        self.s.close()

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
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.bind((server, port))
        except socket.error as e:
            logging.info(str(e))

        try:
            self.s.listen(1)
        except Exception as e:
            self.connected = False
            logging.info('Failed to listen: %s', e)
            return
        logging.info("Waiting for a connection, Server Started")

        while self.players < MAX_PLAYERS:
            try:
                logging.info("[CONNECT] Finding connection!")
                conn, addr = self.s.accept()
                if self.is_ready() or len(self.clients) >= MAX_PLAYERS:
                    break
                self.players += 1
                logging.info(f"[CONNECT] Connected [{self.players}/{MAX_PLAYERS}]!")
                self.authentication(conn, addr)
                self.send_all(f'10_{self.players}_{MAX_PLAYERS}')
            except Exception as ex:
                logging.info('%s', ex)
                return
        # self.waiting = False
        logging.info('Everybody connected.')

    def authentication(self, conn, addr):
        try:
            client = ClientConnection(addr, conn)
            self.clients.append(client)
            self.connected_callback(client)
            thread = threading.Thread(target=self.player_input_thread, args=(client,), daemon=True)
            client.thread = thread
            thread.start()
            logging.info(f"[AUTHENTICATION] Thread for client '{client.id}' started.")
        except Exception as e:
            logging.info("[AUTHENTICATION][ERROR]", e)
            conn.close()

    def player_input_thread(self, client):
        command_buffer = ''
        while self.connected:
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
                logging.info('[PLAYER THREAD ERROR] from client: %d %s', client.id, ex)
                self.clients.remove(client)
                self.disconnected_callback(client)
                self.players -= 1
                logging.info(f"[CONNECT] Disconnected [{self.players}/{MAX_PLAYERS}]!")
                self.send_all(f'10_{self.players}_{MAX_PLAYERS}')
                return


class Player:
    def __init__(self, client):
        self.client: ClientConnection = client
        self.money = MONEY_FROM_START
        self.wood = WOOD_FROM_START
        self.max_forge_level = 0
        self.id = -2
        self.power = 0
        self.nick = 'None'


class ServerGame:
    def __init__(self, server):
        self.lock = Lock()
        self.sprites = Group()
        self.buildings = Group()
        self.players: Dict[int, Player] = {}
        self.server: Server = server
        self.side = SERVER

    def claim_money(self, player_id: int, costs: Tuple[float, float]):
        pl = self.players.get(player_id)
        if pl is None:
            return False
        if pl.money < costs[0]:
            logging.info('Not enough money')
            pl.client.send('8_0_0')
            return False
        if pl.wood < costs[1]:
            logging.info('Not enough wood')
            pl.client.send('8_0_1')
            return False
        pl.money -= costs[0]
        pl.wood -= costs[1]
        pl.client.send(f'3_1_{pl.money}_{pl.wood}')
        return True

    def claim_unit_cost(self, player_id: int, clazz):
        pl = self.players.get(player_id)
        if pl is None:
            return False
        if pl.money < clazz.cost[0]:
            logging.info('Not enough money')
            pl.client.send('8_0_0')
            return False
        if pl.wood < clazz.cost[1]:
            logging.info('Not enough wood')
            pl.client.send('8_0_1')
            return False
        if Farm.get_player_meat(player_id) < pl.power + clazz.power_cost:
            logging.info('Not enough meat')
            pl.client.send('8_0_2')
            return False
        pl.money -= clazz.cost[0]
        pl.wood -= clazz.cost[1]
        pl.power += clazz.power_cost
        pl.client.send(f'3_1_{pl.money}_{pl.wood}')
        pl.client.send(f'3_2_{pl.power}_{Farm.get_player_meat(pl.id)}')
        return True

    def find_losed_players(self):
        self.lock.acquire()
        losed = []
        for pl in self.players.values():
            if Fortress.get_player_level(pl.id) == 0:
                if pl.power < 20:
                    losed.append(pl)
        for pl in losed:
            pl.client.send('12')
            pl.client.disconnect('You lose!!!')
            logging.info('%d lose', pl.id)
        if len(self.players) == 1:
            for i in self.players.values():
                i.client.send('11')
                i.client.disconnect(f'You win, {i.nick}')
        self.lock.release()

    def add_player(self, client: ClientConnection, player_id: int):
        self.lock.acquire()
        p = Player(client)
        p.id = player_id
        p.client.id = player_id
        p.nick = client.nick
        self.players[player_id] = p
        self.lock.release()

    def give_resources(self, player_id: int, costs: Tuple[float, float]):
        pl = self.players.get(player_id)
        if pl is None:
            return
        pl.money += costs[0]
        pl.wood += costs[1]
        pl.client.send(f'3_1_{pl.money}_{pl.wood}')
        pl.client.send(f'3_3_{costs[0]}')
        pl.client.send(f'3_4_{costs[1]}')

    def update(self, *args):
        # self.lock.acquire()
        self.sprites.update(*args)
        # self.lock.release()

    def place(self, build_class, x: int, y: int, player_id: int, *args,
              ignore_space=False, ignore_money=False, ignore_fort_level=False):
        self.lock.acquire()

        building = None
        if ignore_fort_level or build_class.required_level <= Fortress.get_player_level(player_id):
            building = build_class(x, y, get_curr_id(), player_id, *args)
            if ignore_space or (not sprite.spritecollideany(building, self.sprites)):
                if ignore_money or self.claim_money(player_id, build_class.cost):
                    self.server.send_all(
                        f'1_{get_class_id(build_class)}_{x}_{y}_{building.unit_id}_{player_id}{building.get_args()}')
                    self.sprites.add(building)
                    if building.unit_type == TYPE_BUILDING:
                        self.buildings.add(building)
                    if building.can_upgraded:
                        building.next_level(self)
                        self.server.send_all(f'7_{building.unit_id}_{building.level}')
            else:
                self.safe_send(player_id, '8_1')
                building.kill()
                building = None

        self.lock.release()
        return building

    def safe_send(self, player_id: int, msg: str):
        pl = self.players.get(player_id)
        if pl is None:
            return
        pl.client.send(msg)

    def place_building(self, build_class, x, y, player_id):
        self.lock.acquire()

        building = None
        if build_class.required_level <= Fortress.get_player_level(player_id):
            building = UncompletedBuilding(x, y, get_curr_id(), player_id, get_class_id(build_class))
            if not sprite.spritecollideany(building, self.sprites):
                if self.claim_money(player_id, build_class.cost):
                    self.server.send_all(
                        f'1_{get_class_id(UncompletedBuilding)}_{x}_{y}_'
                        f'{building.unit_id}_{player_id}{building.get_args()}')
                    self.sprites.add(building)
                    if building.unit_type == TYPE_BUILDING:
                        self.buildings.add(building)
            else:
                self.safe_send(player_id, '8_1')
                building.kill()
                building = None
        else:
            self.safe_send(player_id, '8_2')

        self.lock.release()
        return building

    def upgrade_building(self, unit_id: int, client: ClientConnection):
        self.lock.acquire()
        en = self.find_with_id(unit_id)
        if en.can_upgraded and en.can_be_upgraded(self):
            *cost, fort_need = en.level_cost(self)
            if fort_need <= Fortress.get_player_level(client.id):
                if self.claim_money(client.id, cost):
                    en.next_level(self)
                    self.server.send_all(f'7_{en.unit_id}_{en.level}')
            else:
                self.safe_send(client.id, '8_2')
        self.lock.release()

    def get_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.sprites, False)

    def get_building_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.buildings, False)

    def retarget(self, unit_id, x, y, client):
        for i in self.sprites:
            if i.unit_id == unit_id:
                if i.unit_type == TYPE_FIGHTER:
                    self.lock.acquire()
                    if i.player_id == client.id:
                        i.set_target(TARGET_MOVE, (x, y), self)
                    self.lock.release()
                    return True
        return False

    def find_with_id(self, unit_id):
        for spr in self.sprites:
            if spr.unit_id == unit_id:
                return spr

    def kill(self, spr):
        self.server.send_all(f'4_{spr.unit_id}')
        spr.kill()

    def remove_player(self, client: ClientConnection):
        self.lock.acquire()
        p = None
        for i, j in self.players.items():
            if j.client == client:
                p = i
                break
        if p is None:
            logging.info(f'No player with {client} {client.id}')
        else:
            for spr in self.sprites:
                if spr.player_id == self.players[p].id:
                    self.kill(spr)
            self.players.pop(p, None)
        self.lock.release()


def place_fortresses(game: ServerGame):
    logging.debug('Placing started.')
    players_count = len(game.players.values())
    angle = 0
    game.place(Mine, -100, -100, -1, ignore_money=True, ignore_fort_level=True, ignore_space=True)
    game.place(Mine, -100, 100, -1, ignore_money=True, ignore_fort_level=True, ignore_space=True)
    game.place(Mine, 100, -100, -1, ignore_money=True, ignore_fort_level=True, ignore_space=True)
    game.place(Mine, 100, 100, -1, ignore_money=True, ignore_fort_level=True, ignore_space=True)
    for player_id, player in game.players.items():
        x, y = cos(radians(angle)), sin(radians(angle))
        angle += 360 / players_count / 2
        x, y = int(x * 3500), int(y * 3500)
        game.place(Fortress, x, y, player_id,
                   ignore_money=True, ignore_fort_level=True, ignore_space=True)
        player.client.send(f'6_{-x + SCREEN_WIDTH // 2}_{-y + SCREEN_HEIGHT // 2}')

        x, y = int(x * 0.8), int(y * 0.8)
        game.place(Mine, x, y, -1,
                   ignore_money=True, ignore_fort_level=True, ignore_space=True)

        stone_x, stone_y = cos(radians(angle)), sin(radians(angle))
        current_x, current_y = stone_x * 350, stone_y * 350
        while abs(current_x) < WORLD_SIZE / 2 + 50 and abs(current_y) < WORLD_SIZE / 2 + 50:
            game.place(Stone, int(current_x), int(current_y), -1,
                       ignore_space=True, ignore_money=True, ignore_fort_level=True)
            current_x, current_y = current_x + stone_x * 100, current_y + stone_y * 100

        angle += 360 / players_count / 2

        trees_left = 15
        tree_x, tree_y = randint(x - 500, x + 500), randint(y - 500, y + 500)
        while trees_left > 0:
            if game.place(Tree, tree_x, tree_y, -1, ignore_money=True, ignore_fort_level=True) is not None:
                trees_left -= 1
            tree_x, tree_y = randint(x - 500, x + 500), randint(y - 500, y + 500)

    forests = []
    for _ in range(FORESTS_COUNT):
        trees_left = TREES_PER_FOREST
        forest_x, forest_y = randint(- WORLD_SIZE // 3, WORLD_SIZE // 3), randint(- WORLD_SIZE // 3, WORLD_SIZE // 3)
        game.server.send_all(f'13_{forest_x}_{forest_y}')
        forests.append((forest_x, forest_y))
        tree_x, tree_y = [randint(forest_x - TREES_RANGE, forest_x + TREES_RANGE),
                          randint(forest_y - TREES_RANGE, forest_y + TREES_RANGE)]
        while trees_left > 0:
            if game.place(Tree, tree_x, tree_y, -1, ignore_money=True, ignore_fort_level=True) is not None:
                trees_left -= 1
            tree_x, tree_y = [randint(forest_x - TREES_RANGE, forest_x + TREES_RANGE),
                              randint(forest_y - TREES_RANGE, forest_y + TREES_RANGE)]

    logging.debug('Placing stopped.')
    return forests


def main(screen, nickname):
    connect_info = [0, 0]

    def pre_read(cmd, args, client):
        logging.info(f'{cmd}, {args}')
        if cmd == '10':  # Player is ready
            connect_info[1] += 1
            logging.info('%s ready', client)
            client.ready = True
            client.nick = args[0]

    def read(cmd, args, client):
        logging.info(f'{cmd}, {args}')
        if cmd == '1':
            game.place_building(UNIT_TYPES[int(args[0])], int(args[1]), int(args[2]), client.id)
        elif cmd == '2':
            game.retarget(*list(map(int, args)), client)
        elif cmd == '3':
            game.lock.acquire()
            en = game.find_with_id(int(args[0]))
            if en is not None:
                en.add_to_queque(UNIT_TYPES[int(args[1])], game)
            game.lock.release()
        elif cmd == '4':
            game.lock.acquire()
            en = game.find_with_id(int(args[0]))
            if type(en) == Worker and en.player_id == client.id:
                en.state = int(args[1])
                en.find_new_target(game, 3000)
            game.lock.release()
        elif cmd == '5':
            game.upgrade_building(int(args[0]), client)
        else:
            logging.info('Invalid command')

    def connect_player(_):
        connect_info[0] += 1

    def disconnect_player(client):
        if client.ready:
            connect_info[1] -= 1
        connect_info[0] -= 1

    def disconnect_player_game(client):
        game.remove_player(client)

    def update_players_info():
        game.lock.acquire()
        for pl in game.players.values():
            pl.client.send(f'3_1_{pl.money}_{pl.wood}')
            pl.client.send(f'3_2_{pl.power}_{Farm.get_player_meat(pl.id)}')
        game.lock.release()

    def place_tree(forest_x, forest_y):
        tree_x, tree_y = [randint(forest_x - TREES_RANGE, forest_x + TREES_RANGE),
                          randint(forest_y - TREES_RANGE, forest_y + TREES_RANGE)]
        attemps = 5
        while attemps > 0:
            if game.place(Tree, tree_x, tree_y, -1, ignore_money=True, ignore_fort_level=True) is not None:
                logging.info(f'Tree placed')
                return
            tree_x, tree_y = [randint(forest_x - TREES_RANGE, forest_x + TREES_RANGE),
                              randint(forest_y - TREES_RANGE, forest_y + TREES_RANGE)]
            attemps -= 1

    global settings
    settings = data.read_settings('settings/server_setting.txt')
    server_ip = settings['IP']
    if server_ip == 'auto':
        server_ip = socket.gethostbyname(socket.gethostname())
    logging.info('Your ip is: %s', server_ip)
    server = Server(server_ip)
    game = ServerGame(server)
    Unit.game = game
    Unit.free_id = FREE_ID
    server.callback = pre_read
    server.connected_callback = connect_player
    server.disconnected_callback = disconnect_player
    thread = threading.Thread(target=server.thread_connection, daemon=True)
    thread.start()
    font = pygame.font.Font("font/NK57.ttf", 40)
    background = pygame.image.load('sprite/data/play.png').convert()
    image = {"host": (330, 250),
             "connect": (330, 455),
             "menu": (340, 700),
             "cancel": (1311, 700)}

    all_buttons = pygame.sprite.Group()
    for n, i in enumerate(image):
        if n < 3:
            if n == 0:
                data.Button(all_buttons, i, image[i], 1)
            else:
                data.Button(all_buttons, i, image[i], 3)
    cancel_buttons = pygame.sprite.Group()
    data.Button(cancel_buttons, "cancel", image["cancel"])
    font1 = pygame.font.Font("font/NK57.ttf", 55)

    while server.connected and not server.is_ready():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            for button in cancel_buttons:
                if button.get_event(event):
                    server.disconnect()
                    return "play"
            for button in all_buttons:
                button.get_event(event)
        screen.blit(background, (0, 0))
        text = font.render(f'Сообщите ip остальным игрокам:', 1, (200, 200, 200))
        screen.blit(text, (650, 310))
        text = font.render(f'[{server_ip}]', 1, (255, 5, 5))
        screen.blit(text, (650, 355))
        text = font.render(f'Подключено [{connect_info[0]}/{MAX_PLAYERS}]', 1, (200, 200, 200))
        screen.blit(text, (650, 405))
        text = font.render(f'Готово: [{connect_info[1]}]', 1, (200, 200, 200))
        screen.blit(text, (650, 455))
        all_buttons.draw(screen)
        cancel_buttons.draw(screen)
        screen.blit(font1.render(nickname, 1, (255, 255, 255)), (810, 745))
        screen.blit(data.cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()

    if not server.connected:
        return "play"

    nicknames = []
    for i, c in enumerate(server.clients):
        game.add_player(c, i)
        nicknames.append(c.nick)
        logging.info('Nick %s', c.nick)
    for i, c in game.players.items():
        c.client.send(f'0_{i}_{"_".join(nicknames)}')

    clock = pygame.time.Clock()

    server.callback = read
    server.disconnected_callback = disconnect_player_game
    running = True
    forests = place_fortresses(game)
    pygame.time.set_timer(SERVER_EVENT_UPDATE, 1000 // 60)
    pygame.time.set_timer(SERVER_EVENT_SEC, 1000 // 1)
    pygame.time.set_timer(SERVER_EVENT_SYNC, 5000)
    background = pygame.image.load('sprite/data/menu.png').convert()
    current_fps, frames = 60, 0
    sync_counter = 0
    plant_delay = 20 - len(game.players)
    plant_timer = 0
    while running and len(game.players) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                server.disconnect()
                exit()
            elif event.type in [SERVER_EVENT_UPDATE, SERVER_EVENT_SEC]:
                game.update(event, game)
                if event.type == SERVER_EVENT_SEC:
                    current_fps = frames
                    frames = 0
                    update_players_info()
            elif event.type == SERVER_EVENT_SYNC:
                if not settings['ONE_PLAYER_MODE']:
                    game.find_losed_players()
                sync_counter += 1
                if sync_counter >= len(game.players):
                    logging.info('Sync')
                    sync_counter = 0
                    game.lock.acquire()
                    for spr in game.sprites:
                        spr.send_updated(game)
                    game.lock.release()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    server.disconnect()
                    return "host"

            if event.type == SERVER_EVENT_SEC:
                plant_timer += 1
                if plant_timer >= plant_delay:
                    forest = choice(forests)
                    place_tree(*forest)

                    plant_timer = 0
        screen.blit(background, (0, 0))
        screen.blit(font.render(f'FPS: {current_fps}', 1, (200, 200, 200)), (0, 0))
        pygame.display.flip()
        frames += 1
        clock.tick(60)
    server.disconnect()
    return "host"
