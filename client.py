import math
import random
import socket
import threading
import time
from threading import Lock

import pygame
from pygame.sprite import Group


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
        while self.connected:
            try:
                if self.callback:
                    commands = self.conn.recv(1024).decode().split(';')
                    for i in commands:
                        if i == '':
                            continue
                        command = i.split('_')
                        cmd, *args = command
                        self.callback(cmd, args, *self.call_args)
            except Exception as ex:
                print('[READ THREAD]', ex)
                print('[READ THREAD] NO LONGER READING FROM SERVER!')
                self.disconnect(ex)
                return


class Bomb(pygame.sprite.Sprite):
    bomb = pygame.image.load('sprites/bomb.png')

    def __init__(self, group, x, y, id):
        self.image = Bomb.bomb
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.id = id
        self.target = None
        super().__init__(group)

    def update(self, *args):
        if self.target is not None:
            xr = self.target[0] - self.rect.centerx
            yr = self.target[1] - self.rect.centery
            if math.sqrt(xr * xr + yr * yr) < 50:
                self.target = None
                return
            x = (-1 if self.target[0] - self.rect.centerx < 0 else 1) if self.target[0] != self.rect.centerx else 0
            y = (-1 if self.target[1] - self.rect.centery < 0 else 1) if self.target[1] != self.rect.centery else 0
            self.rect.move_ip(x, y)


class Game:
    def __init__(self):
        self.sprites = Group()
        self.lock = Lock()
        self.started = False

    def start(self):
        self.started = True

    def drawSprites(self, surface):
        self.lock.acquire()
        self.sprites.draw(surface)
        self.lock.release()

    def addSprite(self, x, y, id):
        self.lock.acquire()
        Bomb(self.sprites, x, y, id)
        self.lock.release()

    def update(self):
        self.sprites.update()

    def retarget(self, id, x, y):
        for i in self.sprites:
            if i.id == id:
                i.target = (x, y)
                return


def waiting_screen(screen, client, game):
    players_info = [0, 0]

    def read(cmd, args):
        print(cmd, args)
        if cmd == '0':
            game.start()
            print('start')
        if cmd == '10':
            players_info[0] = int(args[0])
            players_info[1] = int(args[1])
            print(players_info)

    client.setEventCallback(read)
    clock = pygame.time.Clock()
    running = True
    t, c = 0, 0
    font = pygame.font.Font(None, 30)
    while running and not game.started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((125, 125, 0))
        text = font.render(f'{players_info[0]}/{players_info[1]} players.', 1, (255, 255, 100))
        screen.blit(text, (100, 75))

        t += 1
        c += 1
        if t > 150:
            t = 0
        if c > 360:
            c = 0
        color = pygame.Color('red')
        hsva = color.hsva
        color.hsva = (c, hsva[1], hsva[2], hsva[3])
        for i in range(6):
            if i * 20 < t < i * 20 + 60:
                pygame.draw.ellipse(screen, color, (100 + i * 20, 100, 15, 15))
        pygame.draw.rect(screen, pygame.Color('brown'), (100, 100, 6 * 20 - 5, 15), 1)

        pygame.display.flip()
        clock.tick(60)
    print('Ended')
    if not running:
        client.disconnect('App closed.')
        pygame.quit()
        exit(0)


class SelectArea:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.active = False

    def mouse_moved(self, x, y):
        self.width += x
        self.height += y

    def clear(self):
        self.width = 0
        self.height = 0
        self.active = False

    def draw(self, screen):
        pygame.draw.rect(screen, pygame.Color('blue'), (self.x, self.y, self.width, self.height), 2)

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


def game_screen(screen, client, game):
    def listen(cmd, args):
        # 0 - Game Started
        # 1 - Add object at [x, y]
        # 10 - Tell player count [curr, max]
        print(cmd, args)
        if cmd == '1':
            x, y, id = list(map(int, args))
            print(id)
            game.addSprite(x, y, id)
        elif cmd == '2':
            id, x, y = list(map(int, args))
            game.retarget(id, x, y)
        else:
            print('Taken message:', cmd, args)

    def add_bomb(x, y):
        # game.addSprite(x, y)
        client.send(f'1_{x}_{y}')

    client.setEventCallback(listen)
    time.sleep(1)
    clock = pygame.time.Clock()
    running = True
    current_area = SelectArea()
    for _ in range(2):
        add_bomb(random.randint(0, 300), random.randint(0, 300))
    while running and client.connected:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not current_area.active:
                    current_area.x, current_area.y = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                if current_area.active:
                    for spr in current_area.find_intersect(game.sprites):
                        client.send(f'2_{spr.id}_{event.pos[0]}_{event.pos[1]}')
                    current_area.clear()
                elif current_area.width != 0 and current_area.height != 0:
                    current_area.active = True
                else:
                    add_bomb(event.pos[0] - 50, event.pos[1] - 50)

            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0] == 1 and not current_area.active:
                    current_area.mouse_moved(*event.rel)

        game.update()
        screen.fill((125, 125, 125))
        game.drawSprites(screen)
        current_area.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    client.disconnect('Application closed.')


def main():
    client = Client()
    pygame.init()
    size = 500, 500
    screen = pygame.display.set_mode(size)
    game = Game()
    client.start_thread()

    # Screens
    waiting_screen(screen, client, game)
    game_screen(screen, client, game)

    # End
    pygame.quit()


if __name__ == '__main__':
    main()
