import socket
import threading
from threading import Lock

import pygame
from pygame.sprite import Group


class Client:
    def __init__(self, name, listener):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "localhost"
        self.port = 5556
        self.addr = (self.server, self.port)
        self.name = name
        self.i = 0
        self.connect()
        self.listener = listener

    def start_thread(self):
        thread = threading.Thread(target=self.thread_listen)
        thread.start()

    def connect(self):
        try:
            self.conn.connect(self.addr)
            self.conn.sendall(self.name.encode())
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

    def thread_listen(self):
        while True:
            try:
                command = self.conn.recv(1024)
                self.listener(command.decode())
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

    def drawSprites(self, surface):
        self.lock.acquire()
        self.sprites.draw(surface)
        self.lock.release()

    def addSprite(self, x, y):
        self.lock.acquire()
        Bomb(self.sprites, x, y)
        self.lock.release()


def listen(command):
    print(command)
    # 0 - Game Started
    # 1 - Add object at [x, y]
    if command.startswith('1'):
        x, y = list(map(int, command[2::].split()))
        game.addSprite(x, y)
    else:
        print('Taken message:', command)


# Init
client = Client('test', listen)
while client.conn.recv(1024).decode() != '0':
    pass
pygame.init()
size = 320, 470
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
running = True
game = Game()

client.start_thread()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            game.addSprite(event.pos[0] - 50, event.pos[1] - 50)
            client.send(f'0 1 {event.pos[0] - 50} {event.pos[1] - 50}')
    screen.fill((0, 0, 0))
    game.drawSprites(screen)

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
