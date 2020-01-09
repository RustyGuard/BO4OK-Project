import threading

from ip import Ip
import pygame

from server import Server, ServerGame


def read(cmd, args, client):
    print(cmd, args, client)


def connect_player(client):
    Play.instance.game.add_player(client)
    print(client)


class Play:
    instance = None

    def play(self, screen=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)):
        Play.instance = self
        background = pygame.image.load('sprite-games/play/Основа.png')
        pygame.init()
        screen.blit(background, (0, 0))
        FPS = 60
        image = {"host": (330, 183),
                 "connect": (330, 386),
                 "back": (330, 784)}

        class Button(pygame.sprite.Sprite):
            def __init__(self, group, name):
                super().__init__(group)
                self.stok_image = pygame.image.load(f'sprite-games/play/{name}.png')
                self.anim = pygame.image.load(f'sprite-games/play/anim/{name}.png')
                self.name = name
                self.image = self.stok_image
                self.rect = self.image.get_rect()
                self.rect.topleft = image[name]
                self.condition = False

            def get_anim(self, event):
                if self.rect.collidepoint(event.pos):
                    self.image = self.anim
                else:
                    if self.image == self.anim:
                        self.image = self.stok_image

            def get_event(self, event):
                if self.rect.collidepoint(event.pos):
                    if self.name == "host":
                        Play.instance.server = Server()
                        Play.instance.game = ServerGame(Play.instance.server)
                        Play.instance.server.callback = read
                        Play.instance.server.connected_callback = connect_player
                        thread = threading.Thread(target=Play.instance.server.thread_connection, daemon=True)
                        thread.start()

                        # сдесь клиент должен сделать хост сервера,
                        # если всё удачно то его состояние(self.condition) должно стать HOST
                        # self.condition = "HOST"
                        return
                    if self.name == "connect":
                        Ip.play(screen)
                    if self.name == "back":
                        return True

        class Cursor(pygame.sprite.Sprite):
            def __init__(self, group):
                super().__init__(group)
                self.image = pygame.image.load('sprite-games/menu/cursor.png')
                self.rect = self.image.get_rect()

        all_buttons = pygame.sprite.Group()
        for i in image:
            Button(all_buttons, i)
        running = True
        clock = pygame.time.Clock()
        all_cursor = pygame.sprite.Group()
        cursor = Cursor(all_cursor)
        pygame.mouse.set_visible(0)
        f = False
        while running:
            screen.fill(pygame.Color("white"))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEMOTION:
                    for button in all_buttons:
                        button.get_anim(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for button in all_buttons:
                        a = button.get_event(event)
                        if a:
                            return
            screen.blit(background, (0, 0))
            all_buttons.draw(screen)
            cursor.rect.topleft = pygame.mouse.get_pos()
            all_cursor.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
