import socket
import threading
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
            self.conn.send(data.encode())
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
                    command = self.conn.recv(1024).decode().split('_')
                    cmd, *args = command
                    self.callback(cmd, args, *self.call_args)
            except Exception as ex:
                print('[READ THREAD]', ex)
                print('[READ THREAD] NO LONGER READING FROM SERVER!')
                return


class Bomb(pygame.sprite.Sprite):
    bomb = pygame.image.load('sprites/bomb.png')

    def __init__(self, group, x, y):
        self.image = Bomb.bomb
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        super().__init__(group)


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

    def addSprite(self, x, y):
        self.lock.acquire()
        Bomb(self.sprites, x, y)
        self.lock.release()


def waiting_screen(screen, client, game):
    def read(cmd, args):
        if cmd == '0':
            game.start()
            print('start')

    client.setEventCallback(read)
    clock = pygame.time.Clock()
    running = True
    t, c = 0, 0
    while running and not game.started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((125, 125, 0))

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


def game_screen(screen, client, game):
    def listen(cmd, args):
        # 0 - Game Started
        # 1 - Add object at [x, y]
        if cmd == '1':
            x, y = list(map(int, args))
            game.addSprite(x, y)
        else:
            print('Taken message:', cmd, args)

    client.setEventCallback(listen)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.addSprite(event.pos[0] - 50, event.pos[1] - 50)
                client.send(f'0_1_{event.pos[0] - 50}_{event.pos[1] - 50}')
        screen.fill((125, 125, 125))
        game.drawSprites(screen)
        pygame.display.flip()
        clock.tick(60)
    client.disconnect('Application closed.')


def main():
    client = Client()
    pygame.init()
    size = 320, 470
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
