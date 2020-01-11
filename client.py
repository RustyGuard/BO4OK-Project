import socket
import threading
from threading import Lock

import pygame
import pygame_gui
from pygame import Color
from pygame.rect import Rect
from pygame.sprite import Group, Sprite
from pygame_gui import UIManager
from pygame_gui.elements import UIButton

from constants import CLIENT_EVENT_SEC, CLIENT_EVENT_UPDATE, COLOR_LIST, CAMERA_MIN_SPEED, CAMERA_MAX_SPEED, \
    CAMERA_STEP_FASTER, CAMERA_STEP_SLOWER
from units import Mine, Soldier, get_class_id, UNIT_TYPES, TARGET_MOVE, TARGET_ATTACK, TARGET_NONE, Archer, Arrow, \
    ProductingBuild, Worker, STATE_DIG, STATE_FIGHT, STATE_BUILD, STATE_CHOP


class Client:
    def __init__(self, ip='localhost'):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ip
        self.port = 5556
        self.addr = (self.server, self.port)
        self.connected = False
        self.connect()
        self.callback = None
        self.call_args = []

    def setEventCallback(self, callback, *args):
        self.callback = callback
        self.call_args = args

    def start_thread(self):
        thread = threading.Thread(target=self.thread_listen)
        thread.start()

    def connect(self):
        try:
            self.conn.connect(self.addr)
            self.connected = True
        except Exception as e:
            self.disconnect(e)

    def send(self, data):
        try:
            self.conn.send((data + ';').encode())
        except socket.error as e:
            self.disconnect(e)

    def disconnect(self, msg):
        print("[EXCEPTION] Disconnected from server:", msg)
        self.conn.close()
        self.connected = False

    def thread_listen(self):
        command_buffer = ''
        while self.connected:
            try:
                if self.callback:
                    command_buffer += self.conn.recv(1024).decode()
                    splitter = command_buffer.find(';')
                    while splitter != -1:
                        command = command_buffer[:splitter]
                        if command != '':
                            command = command.split('_')
                            cmd, *args = command
                            self.invoke(cmd, args)
                        command_buffer = command_buffer[splitter + 1:]
                        splitter = command_buffer.find(';')
            except Exception as ex:
                print('[READ THREAD]', ex)
                print('[READ THREAD] NO LONGER READING FROM SERVER!')
                self.disconnect(ex)
                return

    def invoke(self, cmd, args):
        while self.callback is None:
            pass
        self.callback(cmd, args, *self.call_args)


class PlayerInfo:
    def __init__(self):
        self.money = 150.0
        self.wood = 100.0
        self.id = None


class Camera:
    def __init__(self, sprites):
        self.sprites = sprites
        self.off_x = 0
        self.off_y = 0
        self.speed = CAMERA_MIN_SPEED

    def move(self, x, y):
        if x != 0 or y != 0:
            self.off_x += x * int(self.speed)
            self.off_y += y * int(self.speed)
            self.speed += CAMERA_STEP_FASTER
            self.speed = min(CAMERA_MAX_SPEED, self.speed)
            for spr in self.sprites:
                spr.set_offset(self.off_x, self.off_y)
        else:
            self.speed -= CAMERA_STEP_SLOWER
            self.speed = max(CAMERA_MIN_SPEED, self.speed)

    def set_pos(self, x, y):
        self.off_x = x
        self.off_y = y
        for spr in self.sprites:
            spr.set_offset(self.off_x, self.off_y)


class Game:
    def __init__(self):
        self.sprites = Group()
        self.buildings = Group()
        self.lock = Lock()
        self.started = False
        self.info = PlayerInfo()

    def start(self):
        self.started = True

    def drawSprites(self, surface):
        self.lock.acquire()
        self.sprites.draw(surface)
        self.lock.release()

    def addEntity(self, type, x, y, id, player_id, camera, args):
        self.lock.acquire()
        en = UNIT_TYPES[type](x, y, id, player_id, *args)
        en.offsetx = camera.off_x
        en.offsety = camera.off_y
        en.update_rect()
        self.sprites.add(en)
        if en.is_building:
            self.buildings.add(en)
        print(f'Created entity of type [{type}] at [{x}, {y}] owner {player_id}')
        self.lock.release()

    def get_intersect(self, sprite):
        return pygame.sprite.spritecollide(sprite, self.sprites, False)

    def get_building_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.buildings, False)

    def update(self, *args):
        self.sprites.update(*args)

    def retarget(self, id, x, y):
        for i in self.sprites:
            if i.id == id:
                i.set_target(TARGET_MOVE, (x, y))
                return
        print(f'No objects with this id {id}!!!')

    def find_with_id(self, id):
        for spr in self.sprites:
            if spr.id == id:
                return spr


class SelectArea:
    def __init__(self, game, camera, client):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.active = False
        self.game = game
        self.camera = camera
        self.client = client
        self.manager = UIManager(pygame.display.get_surface().get_size())
        UIButton(Rect(5, 5, 50, 50), 'DIG', self.manager, object_id='retarget').type = STATE_DIG
        UIButton(Rect(55, 5, 50, 50), 'FIGHT', self.manager, object_id='retarget').type = STATE_FIGHT
        UIButton(Rect(110, 5, 50, 50), 'CHOP', self.manager, object_id='retarget').type = STATE_CHOP
        UIButton(Rect(165, 5, 50, 50), 'BUILD', self.manager, object_id='retarget').type = STATE_BUILD

    def mouse_moved(self, x, y):
        self.width += x
        self.height += y

    def clear(self):
        self.width = 0
        self.height = 0
        self.active = False

    def draw_ui(self, screen):
        if self.width != 0 and self.height != 0:
            pygame.draw.rect(screen, COLOR_LIST[self.game.info.id], (self.x, self.y, self.width, self.height), 2)
        if self.active:
            self.manager.draw_ui(screen)

    def find_intersect(self, group):
        test = pygame.sprite.Sprite()
        if self.width < 0:
            self.width = -self.width
            self.x -= self.width
        if self.height < 0:
            self.height = -self.height
            self.y -= self.height
        test.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return pygame.sprite.spritecollide(test, group, False)

    def process_events(self, event):
        if self.active:
            self.manager.process_events(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.active:
                self.x, self.y = event.pos
            return False

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                if self.active:
                    for spr in self.find_intersect(self.game.sprites):
                        if spr.has_target and spr.player_id == self.game.info.id:
                            self.client.send(
                                f'2_{spr.id}_{event.pos[0] - self.camera.off_x}_{event.pos[1] - self.camera.off_y}')
                    self.clear()
                elif self.width != 0 and self.height != 0:
                    self.active = True
                else:
                    return False
                return True

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_object_id == 'retarget':
                    for spr in self.find_intersect(self.game.sprites):
                        if type(spr) == Worker and spr.player_id == self.game.info.id:
                            self.client.send(f'4_{spr.id}_{event.ui_element.type}')
                    self.clear()

        if event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[2] == 1 and not self.active:
                self.mouse_moved(*event.rel)
                return True
        return False

    def update(self, *args):
        if self.active:
            self.manager.update(*args)


class PlaceManager:
    def __init__(self, place_func):
        self.place_func = place_func
        self.build_id = None
        self.sprite = Sprite()
        self.group = Group(self.sprite)

    def set_build(self, build_id):
        self.build_id = build_id
        self.sprite.image = UNIT_TYPES[self.build_id].image
        self.sprite.rect = self.sprite.image.get_rect()
        print('Now id is', build_id)

    def process_events(self, event):
        if self.build_id is None:
            print('PlaceManager has empty build_id!!!')
            return
        if event.type == pygame.MOUSEBUTTONUP:
            self.place_func(event.pos, self.build_id)

    def draw_ui(self, screen):
        self.sprite.rect.center = pygame.mouse.get_pos()
        self.group.draw(screen)

    def update(self, *args):
        pass


class ProductManager:
    def __init__(self, screen):
        self.manager = UIManager(screen.get_size())
        self.spr = None

    def set_building(self, spr):
        self.manager.clear_and_reset()
        self.spr = spr
        for i, clazz in enumerate(spr.valid_types):
            b = UIButton(pygame.Rect(55 + 55 * i, 5, 50, 50), clazz.name, self.manager, object_id='product')
            b.build_id = spr.id
            b.class_id = get_class_id(clazz)

    def process_events(self, event):
        self.manager.process_events(event)

    def draw_ui(self, screen):
        if self.spr is not None:
            pygame.draw.rect(screen, COLOR_LIST[self.spr.player_id], self.spr.rect, 1)
        self.manager.draw_ui(screen)

    def update(self, *args):
        self.manager.update(*args)


class ClientWait:
    def play(self, screen=pygame.display.set_mode((0, 0)), ip='localhost'):
        pygame.mouse.set_visible(0)
        client = Client(ip)
        pygame.init()
        if not client.connected:
            return False

        game = Game()
        client.start_thread()

        # Screens
        if not self.waiting_screen(screen, client, game):
            return False
        if not self.game_screen(screen, client, game):
            return False
        return True

    def waiting_screen(self, screen, client, game):
        players_info = [0, 0]

        def read(cmd, args):
            print(cmd, args)
            if cmd == '0':
                client.setEventCallback(None)
                game.info.id = int(args[0])
                game.start()
                print(f'Game started. Our id is {game.info.id}')
            if cmd == '10':
                players_info[0] = int(args[0])
                players_info[1] = int(args[1])
                print(players_info)

        client.setEventCallback(read)
        clock = pygame.time.Clock()
        running = True
        font = pygame.font.Font(None, 50)
        SIRCLE_SIZE = 100
        OFFSET_X = 600
        OFFSET_Y = 500

        manager = UIManager(screen.get_size(), 'sprite-games/themes/theme.json')
        ready_button = UIButton(
            pygame.Rect(OFFSET_X, OFFSET_Y + SIRCLE_SIZE - 100, 355, 91),
            '', manager, object_id='ready')
        background = pygame.image.load('sprite-games/menu/background.png')
        a1 = pygame.image.load('sprite-games/play/ожидание/1.png')
        a2 = pygame.image.load('sprite-games/play/ожидание/2.png')
        a3 = pygame.image.load('sprite-games/play/ожидание/3.png')
        a4 = pygame.image.load('sprite-games/play/ожидание/4.png')
        aa = [a1, a2, a3, a4]
        a = 0
        image1 = pygame.image.load('sprite-games/menu/cursor.png')
        while running and not game.started:
            for event in pygame.event.get():
                manager.process_events(event)
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.USEREVENT:
                    if event.ui_element == ready_button:
                        client.send('10')
                        ready_button.disable()

            manager.update(1 / 60)
            screen.blit(background, (0, 0))
            manager.draw_ui(screen)
            text = font.render(f'{players_info[0]}/{players_info[1]} players.', 1, (200, 200, 200))
            screen.blit(text, (OFFSET_X, OFFSET_Y - SIRCLE_SIZE / 2))
            screen.blit(aa[a // 10], (OFFSET_X + 250, OFFSET_Y - SIRCLE_SIZE / 2))
            screen.blit(image1, pygame.mouse.get_pos())
            a += 1
            if a == 40:
                a = 0
            pygame.display.flip()
            clock.tick(60)
        print('Ended')
        if not running:
            client.disconnect('App closed.')
            return False
        return True

    def game_screen(self, screen, client, game):
        def place(mouse_pos, clazz):
            client.send(f'1_{clazz}_{mouse_pos[0] - camera.off_x}_{mouse_pos[1] - camera.off_y}')

        def listen(cmd, args):
            # 0 - Game Started
            # 1 - Add entity of [type] at [x, y] with [id]
            # 2 - Retarget entity of [type] at [x, y] with [id]
            # 3 - Update Player Info
            # 10 - Tell player count [curr, max]
            print(cmd, args)
            if cmd == '1':
                type, x, y, id, id_player = int(args[0]), int(args[1]), int(args[2]), int(args[3]), int(args[4])
                game.addEntity(type, x, y, id, id_player, camera, args[5::])
                return
            elif cmd == '2':
                if args[0] == str(TARGET_MOVE):
                    id, x, y = int(args[1]), int(args[2]), int(args[3])
                    game.retarget(id, x, y)
                elif args[0] == str(TARGET_ATTACK):
                    id, other_id = int(args[1]), int(args[2])
                    en = game.find_with_id(id)
                    if en:
                        en.set_target(TARGET_ATTACK, game.find_with_id(other_id))
                    else:
                        print('No object with id:', id)
                elif args[0] == str(TARGET_NONE):
                    id = int(args[1])
                    en = game.find_with_id(id)
                    if en:
                        en.set_target(TARGET_NONE, None)
                    else:
                        print('No object with id:', id)
                return
            elif cmd == '3':  # Update Player Info
                if args[0] == '1':  # Money
                    game.info.money = float(args[1])
                    game.info.wood = float(args[2])
                    return
            elif cmd == '4':
                en = game.find_with_id(int(args[0]))
                if en is not None:
                    en.kill()
            elif cmd == '5':
                en = game.find_with_id(int(args[0]))
                en.health = int(args[1])
                en.max_health = int(args[2])
                return
            elif cmd == '6':
                camera.set_pos(int(args[0]), int(args[1]))
                print(camera.off_x, camera.off_y)
            elif cmd == '9':
                game.lock.acquire()
                en = game.find_with_id(int(args[3]))
                if en is None:
                    print('Wasn"t', args)
                    clazz_id = int(args[0])
                    if UNIT_TYPES[clazz_id] == Arrow:
                        en = UNIT_TYPES[int(args[0])](0, 0, 0, 0, 0)
                    else:
                        en = UNIT_TYPES[int(args[0])](0, 0, 0, 0)
                    en.offsetx = camera.off_x
                    en.offsety = camera.off_y
                    game.sprites.add(en)
                    if en.is_building:
                        game.buildings.add(en)

                en.set_update_args(args, game)
                en.update_rect()
                game.lock.release()
                return
            else:
                print('Taken message:', cmd, args)

        font = pygame.font.Font(None, 50)
        client.setEventCallback(listen)
        clock = pygame.time.Clock()
        running = True
        camera = Camera(game.sprites)
        current_area = SelectArea(game, camera, client)
        pygame.time.set_timer(CLIENT_EVENT_UPDATE, 1000 // 60)
        pygame.time.set_timer(CLIENT_EVENT_SEC, 1000 // 1)

        managers = {}
        current_manager = 'main'

        main_manager = UIManager(screen.get_size())
        build_button = UIButton(pygame.Rect(5, 5, 75, 50), 'Build', main_manager)
        retarget_button = UIButton(pygame.Rect(80, 5, 75, 50), 'Retarget', main_manager)

        build_manager = UIManager(screen.get_size())
        UIButton(pygame.Rect(5, 5, 50, 50), 'Back', build_manager, object_id='back')
        build_i = 0
        for build_id, clazz in UNIT_TYPES.items():
            if clazz.placeable:
                b = UIButton(pygame.Rect(55 + 55 * build_i, 5, 50, 50), clazz.name, build_manager, object_id='place')
                b.id = build_id
                build_i += 1

        managers['place'] = PlaceManager(place)
        managers['main'] = main_manager
        managers['build'] = build_manager
        managers['retarget'] = current_area
        managers['product'] = ProductManager(screen)
        image1 = pygame.image.load('sprite-games/menu/cursor.png')

        while running and client.connected:
            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONUP and current_manager == 'main':
                    collided = False
                    for spr in game.buildings:
                        if spr.player_id == game.info.id and spr.rect.collidepoint(event.pos) \
                                and issubclass(type(spr), ProductingBuild):
                            managers['product'].set_building(spr)
                            current_manager = 'product'
                            collided = True
                            break
                    if collided:
                        continue
                managers[current_manager].process_events(event)

                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_object_id == 'back':
                            current_manager = 'main'
                        elif event.ui_object_id == 'place':
                            managers['place'].set_build(event.ui_element.id)
                            current_manager = 'place'
                        elif event.ui_object_id == 'product':
                            btn = event.ui_element
                            client.send(f'3_{btn.build_id}_{btn.class_id}')
                        elif event.ui_element == build_button:
                            current_manager = 'build'
                        elif event.ui_element == retarget_button:
                            current_manager = 'retarget'

                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        if current_manager == 'main':
                            running = False
                        else:
                            current_manager = 'main'

                if event.type in [CLIENT_EVENT_UPDATE, CLIENT_EVENT_SEC]:
                    if event.type == CLIENT_EVENT_UPDATE:
                        x_off, y_off = 0, 0
                        if pygame.key.get_pressed()[pygame.K_w]:
                            y_off += 1
                        if pygame.key.get_pressed()[pygame.K_s]:
                            y_off -= 1
                        if pygame.key.get_pressed()[pygame.K_a]:
                            x_off += 1
                        if pygame.key.get_pressed()[pygame.K_d]:
                            x_off -= 1
                        camera.move(x_off, y_off)
                    game.update(event, game)

            screen.fill((125, 125, 125))
            game.drawSprites(screen)
            for spr in game.sprites:
                if spr.is_projectile or spr.health == spr.max_health:
                    continue
                rect = Rect(spr.rect.left, spr.rect.top - 5, spr.rect.width, 5)
                pygame.draw.rect(screen, Color('red'), rect)
                rect.width = rect.width * spr.health / spr.max_health
                pygame.draw.rect(screen, Color('green'), rect)
                rect.width = spr.rect.width
                pygame.draw.rect(screen, Color('black'), rect, 1)

            text = font.render(str(game.info.money), 1, (100, 255, 100))
            screen.blit(text, (5, 50))
            text = font.render(str(game.info.wood), 1, Color('burlywood'))
            screen.blit(text, (5, 100))
            managers[current_manager].update(1 / 60)
            managers[current_manager].draw_ui(screen)
            screen.blit(image1, pygame.mouse.get_pos())

            pygame.display.flip()
            clock.tick(60)
        client.disconnect('Application closed.')
        return False


def main():
    pygame.init()
    with open('settings.txt', 'r') as settings:
        size = list(map(int, settings.readline().split()))
    ClientWait().play(pygame.display.set_mode(size))
    # End
    pygame.quit()


if __name__ == '__main__':
    main()
