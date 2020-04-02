import logging
import socket
import threading
from random import choice
from threading import Lock
from typing import List, Tuple

from pygame.mixer import Sound, SoundType
from . import data
import pygame_gui
from pygame import Color
from pygame.sprite import Group
from pygame_gui import UIManager
from pygame_gui.elements import UIButton, UILabel

from .units import *

cursor = pygame.image.load('sprite/icon/cursor.png')
clock = pygame.time.Clock()
pygame.mixer.init()
music = data.Music("game", ["game", "game1"])

settings = data.read_settings()
sounds = {
    'build_completed': Sound('music/construction_completed.ogg'),
    'no_money': Sound('music/need_gold.ogg'),
    'no_wood': Sound('music/not_enough_wood.ogg'),
    'no_level': Sound('music/no_level.ogg'),
    'no_meat': Sound('music/build_a_farm.ogg'),
    'no_place': Sound('music/no_place.ogg')
}
current_channel = None


def play_sound(sound: SoundType):
    global current_channel
    if current_channel is not None:
        if current_channel.get_busy():
            return
        current_channel.stop()
    current_channel = sound.play()


def random_nick():
    adj = open('nickname_base/random_adj.txt').readlines()
    noun = open('nickname_base/random_noun.txt').readlines()
    return (choice(adj).replace('\n', '') + ' ' + choice(noun).replace('\n', '')).capitalize()


class Minimap:
    def __init__(self):
        self.rect = Rect(MINIMAP_OFFSETX, 0, MINIMAP_SIZEX, MINIMAP_SIZEY)
        self.rect.bottom = settings['HEIGHT']
        self.font = pygame.font.Font("font/NK57.ttf", 23)
        self.minimap = pygame.image.load('sprite/minimap.png')
        self.marks: List[Tuple[int, int, Color]] = []

    def worldpos_to_minimap(self, pos):
        return self.rect.x + (pos[0] + WORLD_SIZE / 2) / WORLD_SIZE * self.rect.width - MINIMAP_ICON_SIZE / 2, \
               self.rect.y + (pos[1] + WORLD_SIZE / 2) / WORLD_SIZE * self.rect.height - MINIMAP_ICON_SIZE / 2

    def minimap_to_worldpos(self, pos):
        return pos[0] / self.rect.width * WORLD_SIZE - WORLD_SIZE * 0.5, \
               pos[1] / self.rect.height * WORLD_SIZE - WORLD_SIZE * 0.5

    def get_click(self, pos):
        if self.rect.collidepoint(pos[0], pos[1]):
            return self.minimap_to_worldpos((pos[0] - self.rect.x, pos[1] - self.rect.y))
        return None

    def draw(self, camera, game, screen):
        screen.blit(self.minimap, (0, settings['HEIGHT'] - self.minimap.get_height()))
        text = self.font.render(str(game.info.money), 1, (100, 255, 100))
        screen.blit(text, (35, settings['HEIGHT'] - 275))
        text = self.font.render(str(game.info.wood), 1, Color('burlywood'))
        screen.blit(text, (145, settings['HEIGHT'] - 275))
        text = self.font.render(f'{game.info.power}/{game.info.max_power}', 1, Color('palevioletred3'))
        screen.blit(text, (260, settings['HEIGHT'] - 275))

        icon = Rect(0, 0, MINIMAP_ICON_SIZE, MINIMAP_ICON_SIZE)
        for i in game.buildings:
            if isinstance(i, Stone):
                continue
            icon.center = self.worldpos_to_minimap((i.x, i.y))
            pygame.draw.rect(screen, COLOR_LIST[i.player_id], icon)
            if isinstance(i, Fortress):
                color = Color('white')
            elif isinstance(i, UncompletedBuilding):
                color = Color('orange')
            elif issubclass(type(i), ProductingBuild):
                color = Color('red')
            else:
                color = Color('blue')
            pygame.draw.rect(screen, color, icon, 1)

        for i, j, k in self.marks:
            icon.center = self.worldpos_to_minimap((i, j))
            pygame.draw.ellipse(screen, k, icon)

        rect = (self.rect.x + (-camera.off_x + WORLD_SIZE / 2) / WORLD_SIZE * self.rect.width,
                self.rect.y + (-camera.off_y + WORLD_SIZE / 2) / WORLD_SIZE * self.rect.height,
                settings['WIDTH'] / WORLD_SIZE * self.rect.width, settings['HEIGHT'] / WORLD_SIZE * self.rect.height)
        pygame.draw.rect(screen, Color('red'), rect, 1)

        if settings['DEBUG']:
            pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)


class Particle(Sprite):
    all_frames = {}

    def __init__(self, type_building, x, y, camera, particles):
        super().__init__(particles)
        self.cur_frame = 0
        self.x = x
        self.y = y
        if type_building not in Particle.all_frames:
            Particle.all_frames[type_building] = (pygame.image.load(f'sprite/building/{type_building}/smoke/{1}.png'),
                                                  pygame.image.load(f'sprite/building/{type_building}/smoke/{2}.png'),
                                                  pygame.image.load(f'sprite/building/{type_building}/smoke/{3}.png'))
        self.frames = Particle.all_frames[type_building]
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.centerx = self.x + camera.off_x
        self.rect.centery = self.y + camera.off_y

        self.max_lifetime = 2
        self.time = 20
        self.delay = 20

    def set_offset(self, x, y):
        self.rect.centerx = self.x + x
        self.rect.centery = self.y + y

    def update(self, *args):
        if args is None:
            return
        if args[0].type == CLIENT_EVENT_UPDATE:
            self.time -= 1
            if self.time <= 0:
                self.time += self.delay
                self.cur_frame += 1
            if self.cur_frame > self.max_lifetime:
                self.kill()
                return
            self.image = self.frames[self.cur_frame]


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

    def send(self, msg):
        try:
            self.conn.send((msg + ';').encode())
        except socket.error as e:
            self.disconnect(e)

    def disconnect(self, msg):
        logging.info("[EXCEPTION] Disconnected from server: %s", msg)
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
                logging.info('[READ THREAD] %s', ex)
                logging.info('[READ THREAD] NO LONGER READING FROM SERVER!')
                self.disconnect(ex)
                return

    def invoke(self, cmd, args):
        while self.callback is None:
            pass
        self.callback(cmd, args, *self.call_args)


class PlayerInfo:
    def __init__(self, nick=random_nick()):
        self.money = MONEY_FROM_START
        self.wood = WOOD_FROM_START
        self.id = None
        self.nick = nick
        self.power = 0
        self.max_power = 100


class Camera:
    def __init__(self, sprites, particles):
        self.sprites = sprites
        self.particles = particles
        self.off_x = 0
        self.off_y = 0
        self.speed = CAMERA_MIN_SPEED

    def move(self, x, y):
        if x != 0 or y != 0:
            self.off_x += x * int(self.speed)
            self.off_y += y * int(self.speed)
            if self.off_x < -WORLD_SIZE // 2 + settings['WIDTH']:
                self.off_x = -WORLD_SIZE // 2 + settings['WIDTH']
            if self.off_x > WORLD_SIZE // 2:
                self.off_x = WORLD_SIZE // 2
            if self.off_y < -WORLD_SIZE // 2 + settings['HEIGHT']:
                self.off_y = -WORLD_SIZE // 2 + settings['HEIGHT']
            if self.off_y > WORLD_SIZE // 2:
                self.off_y = WORLD_SIZE // 2
            self.speed += CAMERA_STEP_FASTER
            self.speed = min(CAMERA_MAX_SPEED, self.speed)
            for spr in self.sprites:
                spr.set_offset(self.off_x, self.off_y)
            for part in self.particles:
                part.set_offset(self.off_x, self.off_y)

        else:
            self.speed -= CAMERA_STEP_SLOWER
            self.speed = max(CAMERA_MIN_SPEED, self.speed)

    def set_pos(self, x, y):
        self.off_x = x
        self.off_y = y
        if self.off_x < -WORLD_SIZE / 2 + settings['WIDTH']:
            self.off_x = -WORLD_SIZE / 2 + settings['WIDTH']
        if self.off_x > WORLD_SIZE / 2:
            self.off_x = WORLD_SIZE / 2
        if self.off_y < -WORLD_SIZE / 2 + settings['HEIGHT']:
            self.off_y = -WORLD_SIZE / 2 + settings['HEIGHT']
        if self.off_y > WORLD_SIZE / 2:
            self.off_y = WORLD_SIZE / 2

        for part in self.particles:
            part.set_offset(self.off_x, self.off_y)
        for spr in self.sprites:
            spr.set_offset(self.off_x, self.off_y)

    def update(self):
        if settings['CAMERA']:
            p = pygame.mouse.get_pos()
            x_off, y_off = 0, 0
            if p[0] == 0:
                x_off += 1
            elif p[0] + 1 == settings['WIDTH']:
                x_off -= 1
            if p[1] == 0:
                y_off += 1
            elif p[1] + 1 == settings['HEIGHT']:
                y_off -= 1
        else:
            x_off, y_off = 0, 0
            if pygame.key.get_pressed()[pygame.K_w]:
                y_off += 1
            if pygame.key.get_pressed()[pygame.K_s]:
                y_off -= 1
            if pygame.key.get_pressed()[pygame.K_a]:
                x_off += 1
            if pygame.key.get_pressed()[pygame.K_d]:
                x_off -= 1
        self.move(x_off, y_off)


class Game:
    def __init__(self, nick=random_nick()):
        self.sprites = Group()
        self.buildings = Group()
        self.lock = Lock()
        self.started = False
        self.info = PlayerInfo(nick)
        self.other_nicks = []
        self.side = CLIENT

    def get_player_nick(self, player_id):
        return self.other_nicks[player_id]

    def start(self):
        self.started = True

    def drawSprites(self, surface):
        self.sprites.draw(surface)

    def addEntity(self, unit_type, x, y, unit_id, player_id, camera, args):
        self.lock.acquire()
        en = self.find_with_id(unit_id)
        if en:
            logging.warning('Fantom %s', en)
            en.kill()
        en = UNIT_TYPES[unit_type](x, y, unit_id, player_id, *args)
        en.offsetx = camera.off_x
        en.offsety = camera.off_y
        en.update_rect()
        self.sprites.add(en)
        if en.unit_type == TYPE_BUILDING:
            self.buildings.add(en)
        self.lock.release()

    def get_intersect(self, sprite):
        return pygame.sprite.spritecollide(sprite, self.sprites, False)

    def get_building_intersect(self, spr):
        return pygame.sprite.spritecollide(spr, self.buildings, False)

    def update(self, *args):
        self.lock.acquire()
        self.sprites.update(*args)
        self.lock.release()

    def retarget(self, unit_id, x, y):
        self.lock.acquire()
        for i in self.sprites:
            if i.unit_id == unit_id:
                if issubclass(type(i), Fighter):
                    i.set_target(TARGET_MOVE, (x, y))
                self.lock.release()
                return
        logging.info(f'No objects with this id {unit_id}!!!')
        self.lock.release()

    def find_with_id(self, unit_id):
        for spr in self.sprites:
            if spr.unit_id == unit_id:
                return spr


class SelectArea:
    def __init__(self, game, camera, client):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.selected = []
        self.saved = [[] for _ in range(10)]
        self.active = False
        self.dragged = False
        self.game = game
        self.camera = camera
        self.client = client
        self.hided_manager = UIManager(pygame.display.get_surface().get_size(), 'data_games/game_theme.json')
        buttons = [
            ('Копать', STATE_DIG),
            ('Атаковать', STATE_FIGHT),
            ('Рубить', STATE_CHOP),
            ('Строить', STATE_BUILD),
            ('Всё', STATE_ANY_WORK)
        ]
        for i, (name, state) in enumerate(buttons):
            UIButton(Rect(5, 115 + i * 55, 80, 50), name, self.hided_manager, object_id='retarget').type = state

    def mouse_moved(self, x, y):
        self.width += x
        self.height += y
        self.dragged = True

    def clear(self):
        self.width = 0
        self.height = 0
        self.active = False
        self.selected.clear()
        self.dragged = False

    def draw_ui(self, screen):
        if self.width != 0 and self.height != 0:
            pygame.draw.rect(screen, COLOR_LIST[self.game.info.id], (self.x, self.y, self.width, self.height), 2)
        if self.selected:
            self.hided_manager.draw_ui(screen)
        for spr in self.selected:
            if spr is not None:
                pygame.draw.rect(screen, Color('blue'), spr.rect, 2)

    def find_intersect(self):
        test = pygame.sprite.Sprite()
        if self.width < 0:
            self.width = -self.width
            self.x -= self.width
        if self.height < 0:
            self.height = -self.height
            self.y -= self.height
        test.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return pygame.sprite.spritecollide(test, self.game.sprites, False)

    def process_events(self, event):

        if self.selected:
            self.hided_manager.process_events(event)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                self.clear()
                return False

            fs = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8,
                  pygame.K_9, pygame.K_0]
            if event.key in fs:
                index = fs.index(event.key)
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_CTRL:
                    if self.selected:
                        logging.info('Saved %d %s', index, self.selected)
                        self.saved[index] = self.selected.copy()
                elif mods & pygame.KMOD_SHIFT:
                    if self.saved[index]:
                        logging.info('Loaded %d %s', index, self.saved[index])
                        self.clear()
                        self.selected = self.saved[index].copy()
                        self.active = True

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_object_id == 'retarget':
                    if self.active:
                        for spr in self.selected:
                            if spr.alive and isinstance(spr, Worker) and spr.player_id == self.game.info.id:
                                self.client.send(f'4_{spr.unit_id}_{event.ui_element.type}')
                    self.clear()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.active:
                    self.x, self.y = event.pos
            return False

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                if self.active:
                    for spr in self.selected:
                        if spr is None:
                            continue
                        if spr.alive and spr.unit_type == TYPE_FIGHTER and spr.player_id == self.game.info.id:
                            self.client.send(
                                f'2_{spr.unit_id}_{event.pos[0] - int(self.camera.off_x)}_'
                                f'{event.pos[1] - int(self.camera.off_y)}')
                    self.clear()
            elif event.button == 1:
                if self.dragged:
                    for spr in self.find_intersect():
                        if spr.unit_type == TYPE_FIGHTER and spr.player_id == self.game.info.id:
                            self.selected.append(spr)
                    if self.selected:
                        self.active = True
                    self.dragged = False
                    self.width = 0
                    self.height = 0
                    return True
                return False

        if event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0] == 1 and not self.active:
                self.mouse_moved(*event.rel)
                return True
        return False

    def update(self, *args):
        if self.selected:
            self.hided_manager.update(*args)


class MainManager:
    def __init__(self, game, camera, client, current_manager, managers):
        self.game = game
        self.camera = camera
        self.client = client
        self.current_manager = current_manager
        self.managers = managers
        self.manager = UIManager(pygame.display.get_surface().get_size(), 'data_games/game_theme.json')
        build_i = 0
        for build_id, clazz in UNIT_TYPES.items():
            if clazz.placeable:
                r1 = Rect(settings['WIDTH'] - 65, 45 + 75 * build_i, 50, 50)
                b = UIButton(r1, '', self.manager,
                             object_id=f'place_{build_id}')
                r2 = Rect(0, 0, len(clazz.name) * 9, 25)
                r2.centery = r1.centery
                r2.right = r1.left - 5
                UILabel(r2, clazz.name, self.manager)

                b.id = build_id
                build_i += 1

    def draw_ui(self, screen):
        self.manager.draw_ui(screen)

    def process_events(self, event):
        self.manager.process_events(event)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                collided = False
                for spr in self.game.buildings:
                    if spr.player_id == self.game.info.id and spr.rect.collidepoint(event.pos) \
                            and (issubclass(type(spr), ProductingBuild) or spr.can_upgraded):
                        self.managers['product'].set_building(spr)
                        self.current_manager[0] = 'product'
                        collided = True
                        break
                if collided:
                    return

    def update(self, *args):
        self.manager.update(*args)


class PlaceManager:
    def __init__(self, place_func):
        self.place_func = place_func
        self.build_id = None
        self.sprite = Sprite()
        self.group = Group(self.sprite)
        self.manager = UIManager(pygame.display.get_surface().get_size())

    def set_build(self, build_id):
        self.build_id = build_id
        self.sprite.image = UNIT_TYPES[self.build_id].image
        self.sprite.rect = self.sprite.image.get_rect()
        self.manager.clear_and_reset()
        txt = 'Требования:'
        r2 = Rect(5, 25, len(txt) * 9, 25)
        UILabel(r2, txt, self.manager)
        txt = f'{UNIT_TYPES[build_id].cost[0]} Монет; {UNIT_TYPES[build_id].cost[1]} Дерева'
        r2 = Rect(5, 55, len(txt) * 9, 25)
        UILabel(r2, txt, self.manager)
        txt = f'{UNIT_TYPES[build_id].required_level} Уровень крепости'
        r2 = Rect(5, 85, len(txt) * 9, 25)
        UILabel(r2, txt, self.manager)

    def process_events(self, event):
        if self.build_id is None:
            logging.warning('PlaceManager has empty build_id!!!')
            return
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.place_func(event.pos, self.build_id)

    def draw_ui(self, screen):
        self.sprite.rect.center = pygame.mouse.get_pos()
        self.group.draw(screen)
        self.manager.draw_ui(screen)

    def update(self, *args):
        pass


class ProductManager:
    def __init__(self, screen):
        self.manager = UIManager(screen.get_size(), 'data_games/game_theme.json')
        self.spr = None

    def set_building(self, spr):
        self.manager.clear_and_reset()
        self.spr = spr
        max_i = -1
        if issubclass(type(spr), ProductingBuild):
            for i, clazz in enumerate(spr.valid_types):
                r1 = Rect(settings['WIDTH'] - 65, 45 + 75 * i, 50, 50)
                b = UIButton(r1, '', self.manager,
                             object_id=f'product_{get_class_id(clazz)}')
                r2 = Rect(0, 0, 75, 25)
                r2.centery = r1.centery
                r2.right = r1.left
                UILabel(r2, clazz.name, self.manager)
                b.build_id = spr.unit_id
                b.class_id = get_class_id(clazz)
                max_i = i
        if spr.can_upgraded and len(spr.level_costs) >= spr.level:
            r1 = Rect(settings['WIDTH'] - 65, 45 + 75 * (max_i + 1), 50, 50)
            b = UIButton(r1, '', self.manager,
                         object_id=f'upgrade')
            r2 = Rect(0, 0, 75, 25)
            r2.centery = r1.centery
            r2.right = r1.left
            UILabel(r2, 'Улучшить', self.manager)
            b.build_id = spr.unit_id

            txt = 'Требования:'
            r2 = Rect(5, 25, len(txt) * 9, 25)
            UILabel(r2, txt, self.manager)
            costs = spr.level_costs[spr.level - 1]
            txt = f'{costs[0]} Монет; {costs[1]} Дерева'
            r2 = Rect(5, 55, len(txt) * 9, 25)
            UILabel(r2, txt, self.manager)
            txt = f'{costs[2]} Уровень крепости'
            r2 = Rect(5, 85, len(txt) * 9, 25)
            UILabel(r2, txt, self.manager)

    def process_events(self, event):
        self.manager.process_events(event)

    def draw_ui(self, screen):
        if self.spr is not None:
            pygame.draw.rect(screen, COLOR_LIST[self.spr.player_id], self.spr.rect, 1)
        self.manager.draw_ui(screen)

    def update(self, *args):
        self.manager.update(*args)


class ClientWait:
    def play(self, screen=pygame.display.set_mode((0, 0)), ip='localhost', nick=''):
        client = Client(ip)
        if not client.connected:
            return [None, None]

        game = Game(nick if nick != '' else random_nick())
        client.start_thread()

        # Screens
        if not self.waiting_screen(screen, client, game, nick):
            return [None, None]

        music.game_sounds_play()
        result = self.game_screen(screen, client, game)
        music.all_stop()
        return result

    def waiting_screen(self, screen, client, game, nickname):
        global cursor, clock
        players_info = [0, 0]

        def read(cmd, args):
            logging.debug('%s %s', cmd, args)
            if cmd == '0':
                client.setEventCallback(None)
                game.info.id = int(args[0])
                game.other_nicks.extend(args[1::])
                game.start()
                logging.debug(f'Game started. Our id is {game.info.id}')
            if cmd == '10':
                players_info[0] = int(args[0])
                players_info[1] = int(args[1])
                logging.debug(players_info)

        client.setEventCallback(read)
        background = pygame.image.load('sprite/data/play.png').convert()
        image = {"host": (330, 250),
                 "connect": (330, 455),
                 "menu": (340, 700),
                 "ready": (1311, 700)}

        all_buttons = pygame.sprite.Group()
        for n, i in enumerate(image):
            if n == 1:
                data.Button(all_buttons, i, image[i], 1)
            if n == 0:
                data.Button(all_buttons, i, image[i], 3)

        ready_btn = data.Button(all_buttons, 'ready', (1311, 700))
        ready_btn.enabled = True

        back_buttons = pygame.sprite.Group()
        data.Button(back_buttons, "menu", image["menu"])

        list_expectation = [pygame.image.load(f'sprite/data/expectation/{i}.png') for i in range(1, 5)]
        anim_expectation_number = 0

        running = True
        font = pygame.font.Font("font/NK57.ttf", 55)

        while running and not game.started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                for button in back_buttons:
                    if button.get_event(event):
                        client.disconnect('exit')
                        return False
                if ready_btn.enabled and ready_btn.get_event(event):
                    client.send(f'10_{game.info.nick}')
                    ready_btn.enabled = False
            screen.blit(background, (0, 0))
            all_buttons.draw(screen)
            back_buttons.draw(screen)
            text = font.render(f'{players_info[0]}/{players_info[1]} игроков.', 1, (255, 255, 255))
            screen.blit(text, (700, 400))
            screen.blit(font.render(nickname, 1, (255, 255, 255)), (810, 740))
            screen.blit(list_expectation[anim_expectation_number // 10], (900, 300))
            screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
            anim_expectation_number += 1
            if anim_expectation_number == 40:
                anim_expectation_number = 0
            pygame.display.flip()
            clock.tick(60)
        logging.debug('Ended')
        if not running:
            client.disconnect('App closed.')
            return False
        return True

    def game_screen(self, screen, client, game):
        global settings
        stats = {
            'wood_chopped': 0.0,
            'money_mined': 0.0,
            'units_created': 0,
            'build_created': 0
        }

        def place(mouse_pos, clazz):
            client.send(f'1_{clazz}_{mouse_pos[0] - int(camera.off_x)}_{mouse_pos[1] - int(camera.off_y)}')

        def listen(cmd, args):
            try:
                if settings['DEBUG']:
                    logging.debug('%s %s', cmd, args)

                if cmd == '1':  # Add entity of [type] at [x, y] with [id]
                    unit_type, x, y, unit_id, id_player = int(args[0]), int(args[1]), int(args[2]), int(args[3]), int(
                        args[4])
                    game.addEntity(unit_type, x, y, unit_id, id_player, camera, args[5::])
                elif cmd == '2':  # Retarget entity of [type] at [x, y] with [id]
                    if args[0] == str(TARGET_MOVE):
                        unit_id, x, y = int(args[1]), int(args[2]), int(args[3])
                        game.retarget(unit_id, x, y)
                    elif args[0] == str(TARGET_ATTACK):
                        game.lock.acquire()
                        unit_id, other_id = int(args[1]), int(args[2])
                        en = game.find_with_id(unit_id)
                        if en:
                            if issubclass(type(en), Fighter):
                                en.set_target(TARGET_ATTACK, game.find_with_id(other_id))
                        else:
                            logging.debug('No object with id: %d', unit_id)
                        game.lock.release()
                    elif args[0] == str(TARGET_NONE):
                        game.lock.acquire()
                        unit_id = int(args[1])
                        en = game.find_with_id(unit_id)
                        if en:
                            if issubclass(type(en), Fighter):
                                en.set_target(TARGET_NONE, None)
                        else:
                            logging.debug('No object with id: %d', unit_id)
                        game.lock.release()
                elif cmd == '3':  # Update Player Info
                    if args[0] == '1':  # Money
                        game.info.money = float(args[1])
                        game.info.wood = float(args[2])
                    elif args[0] == '2':  # Power
                        game.info.power = int(args[1])
                        game.info.max_power = int(args[2])
                    elif args[0] == '3':  # Money mined
                        stats['money_mined'] += float(args[1])
                    elif args[0] == '4':  # Wood chopped
                        stats['wood_chopped'] += float(args[1])
                    elif args[0] == '5':  # Unit created
                        stats['build_created'] += 1
                        play_sound(sounds['build_completed'])
                    elif args[0] == '6':  # Building completed
                        stats['units_created'] += 1

                elif cmd == '4':
                    game.lock.acquire()
                    en = game.find_with_id(int(args[0]))
                    if en is not None:
                        en.kill()
                    game.lock.release()
                elif cmd == '5':
                    game.lock.acquire()
                    en = game.find_with_id(int(args[0]))
                    en.health = float(args[1])
                    en.max_health = float(args[2])
                    game.lock.release()
                elif cmd == '6':
                    camera.set_pos(int(args[0]), int(args[1]))
                    logging.debug('Camera position setted by server %d %d', camera.off_x, camera.off_y)
                elif cmd == '7':
                    game.lock.acquire()
                    en = game.find_with_id(int(args[0]))
                    en.level = int(args[1])
                    en.update_image()
                    if current_manager[0] == 'product' and managers[current_manager[0]].spr == en:
                        managers[current_manager[0]].set_building(managers[current_manager[0]].spr)
                    game.lock.release()
                elif cmd == '8':
                    if args[0] == '0':
                        if args[1] == '0':
                            play_sound(sounds['no_money'])
                            logging.info('No money')
                        elif args[1] == '1':
                            play_sound(sounds['no_wood'])
                            logging.info('No wood')
                        elif args[1] == '2':
                            play_sound(sounds['no_meat'])
                            logging.info('No meat')
                    elif args[0] == '1':
                        play_sound(sounds['no_place'])
                        logging.info('No place')
                    elif args[0] == '2':
                        play_sound(sounds['no_level'])
                        logging.info('No fort level')
                elif cmd == '9':
                    game.lock.acquire()
                    en = game.find_with_id(int(args[3]))
                    if en is None:
                        logging.warning('Wasn"t %s', args)
                        clazz_id = int(args[0])
                        if UNIT_TYPES[clazz_id] == Arrow:
                            en = UNIT_TYPES[int(args[0])](0, 0, 0, 0, 0)
                        elif UNIT_TYPES[clazz_id] == BallistaArrow:
                            en = UNIT_TYPES[int(args[0])](0, 0, 0, 0, 0)
                        elif UNIT_TYPES[clazz_id] == FireProjectile:
                            en = UNIT_TYPES[int(args[0])](0, 0, 0, 0, 0)
                        else:
                            en = UNIT_TYPES[int(args[0])](0, 0, 0, 0)
                        en.offsetx = camera.off_x
                        en.offsety = camera.off_y
                        game.sprites.add(en)
                        if en.unit_type == TYPE_BUILDING:
                            game.buildings.add(en)

                    en.set_update_args(args, game)
                    en.update_rect()
                    game.lock.release()

                elif cmd == '11':
                    win[0] = True
                elif cmd == '12':
                    win[0] = False
                elif cmd == '13':
                    minimap.marks.append((int(args[0]), int(args[1]), Color('green')))
                else:
                    logging.info('Taken message: %s %s', cmd, args)
            except Exception as ex:
                game.lock.release()
                logging.info('[WARNING] %s', ex)

        Unit.free_id = None
        win = [None]
        background = pygame.image.load('sprite/small_map.png').convert()
        settings = data.read_settings()
        minimap = Minimap()
        particles = Group()
        small_font = pygame.font.Font("font/NK57.ttf", 18)
        fps_font = pygame.font.Font("font/NK57.ttf", 30)
        running = True
        client.setEventCallback(listen)
        camera = Camera(game.sprites, particles)

        pygame.time.set_timer(CLIENT_EVENT_UPDATE, 1000 // 60)
        pygame.time.set_timer(CLIENT_EVENT_SEC, 1000 // 1)

        current_manager = ['main']

        managers = {}
        main_manager = MainManager(game, camera, client, current_manager, managers)
        managers['main'] = main_manager
        managers['place'] = PlaceManager(place)
        managers['product'] = ProductManager(screen)
        logging.info(game.other_nicks)
        fps_count, frames = 60, 0

        camera_area = Sprite()
        camera_area.rect = Rect(0, 0, 1920, 1080)

        select_area = SelectArea(game, camera, client)

        while running and client.connected:
            if win[0] is not None:
                return win[0], stats, game.sprites
            for event in pygame.event.get():
                if select_area.process_events(event):
                    continue

                managers[current_manager[0]].process_events(event)
                if settings['PARTICLES']:
                    particles.update(event)
                if event.type == pygame.MOUSEBUTTONUP:
                    click = minimap.get_click(event.pos)
                    if click is not None:
                        camera.set_pos(-click[0] + settings['WIDTH'] * 0.5, -click[1] + settings['HEIGHT'] * 0.5)
                        continue

                # /* Проверка на нажатие одной из кнопок мэнеджеров
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_object_id == 'back':
                            current_manager[0] = 'main'
                        elif event.ui_object_id.startswith('place'):
                            managers['place'].set_build(event.ui_element.id)
                            current_manager[0] = 'place'
                        elif event.ui_object_id.startswith('product'):
                            btn = event.ui_element
                            client.send(f'3_{btn.build_id}_{btn.class_id}')
                        elif event.ui_object_id.startswith('upgrade'):
                            client.send(f'5_{event.ui_element.build_id}')
                # */

                if event.type == pygame.QUIT:
                    client.disconnect('Application closed.')
                    return False, stats, game.sprites
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        current_manager[0] = 'main'
                    elif event.key == pygame.K_F12:
                        client.disconnect('Application closed.')
                        return False, stats, game.sprites
                    elif event.key == pygame.K_F3:
                        settings['FPS'] = not settings['FPS']
                        data.write_settings(settings)
                    elif event.key == pygame.K_F4:
                        settings['DEBUG'] = not settings['DEBUG']
                        data.write_settings(settings)
                    elif event.key == pygame.K_F9:
                        data.settings(screen, music)
                        settings = data.read_settings()

                if event.type == CLIENT_EVENT_UPDATE:
                    camera.update()

                if event.type in [CLIENT_EVENT_UPDATE, CLIENT_EVENT_SEC]:
                    game.update(event, game)  # Обновление всех юнитов

                if event.type == CLIENT_EVENT_SEC:
                    fps_count = frames
                    frames = 0
                    # /* Создание партиклов дыма
                    if settings['PARTICLES']:
                        for entity in pygame.sprite.spritecollide(camera_area, game.sprites, False):
                            if isinstance(entity, Workshop):
                                Particle('workshop', entity.x, entity.y, camera, particles)
                            elif isinstance(entity, Forge):
                                Particle('forge', entity.x, entity.y, camera, particles)
                            elif isinstance(entity, Farm):
                                Particle('farm', entity.x, entity.y, camera, particles)
                    # */

            # /* Отрисовка
            if settings["BACKGROUND"]:
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        screen.blit(background, (camera.off_x % 965 + j * 965, camera.off_y % 545 + i * 545))
            else:
                screen.fill((96, 128, 56))

            game.lock.acquire()
            game.drawSprites(screen)
            if settings['PARTICLES']:
                particles.draw(screen)
            for spr in pygame.sprite.spritecollide(camera_area, game.sprites, False):
                if spr.can_upgraded:
                    text = small_font.render(f'{spr.level} lvl.', 1, (255, 125, 0))
                    screen.blit(text, spr.rect.topleft)
                if isinstance(spr, Fortress):
                    text = small_font.render(game.get_player_nick(spr.player_id), 1, COLOR_LIST[spr.player_id])
                    screen.blit(text, spr.rect.bottomleft)

                if spr.unit_type == TYPE_PROJECTILE or (spr.health == spr.max_health and not settings['DEBUG']):
                    continue
                colors = ['gray', 'orange'] if isinstance(spr, UncompletedBuilding) else ['red', 'green']
                rect = Rect(spr.rect.left, spr.rect.top - 5, spr.rect.width, 5)
                pygame.draw.rect(screen, Color(colors[0]), rect)
                rect.width = rect.width * spr.health / spr.max_health
                pygame.draw.rect(screen, Color(colors[1]), rect)
                rect.width = spr.rect.width
                pygame.draw.rect(screen, Color('black'), rect, 1)

                if settings['DEBUG']:
                    text = small_font.render(str(spr.health), 1, COLOR_LIST[spr.player_id])
                    screen.blit(text, spr.rect.bottomright)
                    text = small_font.render(str(spr.max_health), 1, COLOR_LIST[spr.player_id])
                    screen.blit(text, spr.rect.topright)

            minimap.draw(camera, game, screen)

            managers[current_manager[0]].update(1 / 60)
            managers[current_manager[0]].draw_ui(screen)
            select_area.draw_ui(screen)
            screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
            if settings['FPS']:
                text = fps_font.render(f'{fps_count}', 1, pygame.Color('red' if fps_count < 40 else 'green'))
                screen.blit(text, (0, 0))

            game.lock.release()
            pygame.display.flip()
            # */
            frames += 1
            clock.tick(60)

        client.disconnect('Application closed.')
        return win[0], stats, game.sprites
