import pygame

import client


class Ip:
    def play(self, screen=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)):
        background = pygame.image.load('sprite-games/play/ip Пример.png')
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
                        if client.ClientWait().play(screen, ip if ip != '' else 'localhost'):
                            return "connect"
                        pygame.mouse.set_visible(False)
                        # сдесь клиент должен подключится к введённому айпи(ip), если удачно должен вернуть "connect",
                        # если нет - то "not_connect"
                        return "not_connect"
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
