import threading

import pygame

import server
from client import ClientWait
from server import Server, ServerGame


def read(cmd, args, client):
    print(cmd, args, client)


def connect_player(client):
    Play.instance.game.add_player(client)
    print(client)


class Play:
    instance = None
    condition = "user"
    readiness = False
    nicname = ""

    def ip(self, screen=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)):
        background = pygame.image.load('sprite-games/play/ip основа.png')
        not_connect = pygame.image.load('sprite-games/play/neconectitsya.png')
        pygame.init()
        screen.blit(background, (0, 0))
        FPS = 60
        image = {"OK": (1085, 709),
                 "back": (558, 709),
                 "ip": (565, 442)}

        class Button(pygame.sprite.Sprite):
            def __init__(self, group, name):
                super().__init__(group)
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
                    if self.name == "OK":
                        print(Play.nicname)
                        print(ip)
                        ClientWait().play(screen, ip if ip != '' else 'localhost')
                        pygame.mouse.set_visible(0)
                        return "back"
                    if self.name == "back":
                        return "back"

        class Cursor(pygame.sprite.Sprite):
            def __init__(self, group):
                super().__init__(group)
                self.image = pygame.image.load('sprite-games/menu/cursor.png')
                self.rect = self.image.get_rect()

        all_buttons = pygame.sprite.Group()
        ip = ""
        for i in image:
            Button(all_buttons, i)
        running = True
        clock = pygame.time.Clock()
        all_cursor = pygame.sprite.Group()
        cursor = Cursor(all_cursor)
        pygame.mouse.set_visible(0)
        font = pygame.font.Font(None, 100)
        f = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEMOTION:
                    for button in all_buttons:
                        button.get_anim(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for button in all_buttons:
                        a = button.get_event(event)
                        if a == "back":
                            return True
                        if a == "connect":
                            return "connect"
                        if a == "not_connect":
                            f = True
                if event.type == pygame.KEYDOWN:
                    if event.unicode in "1234567890.:":
                        ip += event.unicode
                    if event.key == 8:
                        ip = ip[:-1]
            screen.blit(background, (0, 0))
            all_buttons.draw(screen)
            cursor.rect.topleft = pygame.mouse.get_pos()
            screen.blit(font.render(ip, 1, (255, 255, 255)), (565, 460))
            if f:
                screen.blit(not_connect, (650, 600))
            all_cursor.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)

    def play(self, screen=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)):
        Play.instance = self
        background = pygame.image.load('sprite-games/play/Основа.png')
        pygame.init()
        screen.blit(background, (0, 0))
        FPS = 60
        image = {"host": (330, 183),
                 "connect": (330, 386),
                 "back": (330, 784),
                 "ready": (1311, 784),
                 "cancel": (1311, 784)}

        class Button(pygame.sprite.Sprite):
            def __init__(self, group, name):
                super().__init__(group)
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
                    if self.name == "host":
                        server.main(screen)
                        Play.condition = "HOST"
                        Play.readiness = True
                        pygame.mouse.set_visible(0)
                    if self.name == "connect":
                        Play.ip(screen)
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
                Button(all_buttons, i)
        cancel_buttons = pygame.sprite.Group()
        Button(cancel_buttons, "cancel")
        ready_buttons = pygame.sprite.Group()
        Button(ready_buttons, "ready")
        running = True
        clock = pygame.time.Clock()
        all_cursor = pygame.sprite.Group()
        cursor = Cursor(all_cursor)
        pygame.mouse.set_visible(0)
        font = pygame.font.Font(None, 100)
        while running:
            screen.fill(pygame.Color("white"))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        return
                if event.type == pygame.MOUSEMOTION:
                    for button in all_buttons:
                        button.get_anim(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for button in all_buttons:
                        a = button.get_event(event)
                        if a:
                            return
                if event.type == pygame.KEYDOWN:
                    if event.unicode in "ёйцукенгшщзхъфывапролджэячсмить" \
                                        "бюqwertyuiopasdfghjklzxcvbnm1234567890" or \
                            event.unicode in "ёйцукенгшщзхъфывапролджэячсми" \
                                             "тьбюqwertyuiopasdfghjklzxcvbnm1234567890".upper():
                        Play.nicname += event.unicode
                    if event.key == 8:
                        Play.nicname = Play.nicname[:-2]
            screen.blit(background, (0, 0))
            all_buttons.draw(screen)
            cursor.rect.topleft = pygame.mouse.get_pos()
            screen.blit(font.render(Play.nicname, 1, (255, 255, 255)), (810, 810))
            all_cursor.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
