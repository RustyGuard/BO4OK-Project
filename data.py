import pygame
import server
from client import ClientWait

cursor = pygame.image.load('sprite-games/menu/cursor.png')
FPS = 60
clock = pygame.time.Clock()
nicname = ""


class Button(pygame.sprite.Sprite):
    def __init__(self, group, name, image, way):
        super().__init__(group)
        self.stok_image = pygame.image.load(f'sprite-games/{way}/{name}.png')
        self.anim = pygame.image.load(f'sprite-games/{way}/anim/{name}.png')
        self.name = name
        self.image = self.stok_image
        self.rect = self.image.get_rect()
        self.rect.topleft = image

    def get_anim(self, event):
        if self.rect.collidepoint(event.pos):
            self.image = self.anim
        else:
            if self.image == self.anim:
                self.image = self.stok_image


def menu(screen):
    global cursor, FPS, clock
    background = pygame.image.load('sprite-games/menu/background.png')
    screen.blit(background, (0, 0))
    image = {"play": (28, 950),
             "settings": (400, 950),
             "statistics": (772, 950),
             "creators": (1145, 950),
             "exit": (1590, 950)}
    way = "menu"

    all_buttons = pygame.sprite.Group()
    for i in image:
        Button(all_buttons, i, image[i], way)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.MOUSEMOTION:
                for button in all_buttons:
                    button.get_anim(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in all_buttons:
                    if button.rect.collidepoint(event.pos):
                        if button.name == "play":
                            play(screen)
                        if button.name == "settings":
                            pass
                        if button.name == "statistics":
                            pass
                        if button.name == "creators":
                            pass
                        if button.name == "exit":
                            return
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def headpiece(screen):
    FPS = 200
    Bo4ok = pygame.image.load('sprite-games/headpiece/Bo4ok.png')
    Games = pygame.image.load('sprite-games/headpiece/Games.png')
    Potick1 = pygame.image.load('sprite-games/headpiece/Potick1.png')
    Potick2 = pygame.image.load('sprite-games/headpiece/Potick2.png')
    Stone = pygame.image.load('sprite-games/headpiece/Stone.png')
    Water = pygame.image.load('sprite-games/headpiece/Water.png')
    Bo4ok_rect = [-900, 500]
    Potick1_rect = [-400, 500]
    running = True
    clock = pygame.time.Clock()
    Timer = 0
    f = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return
        if Bo4ok_rect[0] < 232:
            Bo4ok_rect[0] += 10
            Potick1_rect[0] += 10
        else:
            Potick1 = Potick2
            Bo4ok_rect[0] = 410
            Potick1_rect[0] = 910
            if not f:
                Timer += 1
                if Timer == 101:
                    f = True
                    Timer = 0
            if Timer == 300:
                return
            else:
                Timer += 1
        screen.fill(pygame.Color("white"))
        screen.blit(Stone, (1170, 500))
        screen.blit(Bo4ok, Bo4ok_rect)
        screen.blit(Potick1, Potick1_rect)
        screen.blit(Games, (1350, 500))
        if f:
            screen.blit(Water, (990, 558))
        pygame.display.flip()
        clock.tick(FPS)


def ip(screen):
    global cursor, FPS, clock, nicname
    background = pygame.image.load('sprite-games/play/ip основа.png')
    not_connect = pygame.image.load('sprite-games/play/neconectitsya.png')
    screen.blit(background, (0, 0))
    image = {"OK": (1085, 709),
             "back": (558, 709),
             "ip": (565, 442)}
    way = "play"
    ip = ""
    f = False

    all_buttons = pygame.sprite.Group()
    for i in image:
        Button(all_buttons, i, image[i], way)
    font = pygame.font.Font(None, 100)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.MOUSEMOTION:
                for button in all_buttons:
                    button.get_anim(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in all_buttons:
                    if button.rect.collidepoint(event.pos):
                        if button.name == "OK":
                            print(nicname)
                            print(ip)
                            if ClientWait().play(screen, ip if ip != '' else 'localhost', nick=nicname):
                                return
                            else:
                                f = True
                        if button.name == "back":
                            return
            if event.type == pygame.KEYDOWN:
                if event.unicode in "1234567890.:":
                    ip += event.unicode
                if event.key == 8:
                    ip = ip[:-1]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(ip, 1, (255, 255, 255)), (565, 460))
        if f:
            screen.blit(not_connect, (650, 600))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def play(screen):
    global cursor, FPS, clock, nicname
    background = pygame.image.load('sprite-games/play/Основа.png')
    screen.blit(background, (0, 0))
    FPS = 60
    image = {"host": (330, 183),
             "connect": (330, 386),
             "back": (330, 784)}
    way = "play"

    all_buttons = pygame.sprite.Group()
    for n, i in enumerate(image):
        if n < 3:
            Button(all_buttons, i, image[i], way)
    font = pygame.font.Font(None, 100)
    while True:
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
                    if button.rect.collidepoint(event.pos):
                        if button.name == "host":
                            server.main(screen)
                        if button.name == "connect":
                            ip(screen)
                        if button.name == "back" or button.name == "cancel":
                            return
            if event.type == pygame.KEYDOWN:
                if event.unicode in "ёйцукенгшщзхъфывапролджэячсмить" \
                                    "бюqwertyuiopasdfghjklzxcvbnm1234567890" or \
                        event.unicode in "ёйцукенгшщзхъфывапролджэячсми" \
                                         "тьбюqwertyuiopasdfghjklzxcvbnm1234567890".upper():
                    nicname += event.unicode
                if event.key == 8:
                    nicname = nicname[:-2]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(nicname, 1, (255, 255, 255)), (810, 810))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


class GameInterface:
    def __init__(self):
        self.panel = pygame.image.load('sprite-games/панель справа/панель справа.png')
        image = {"farm": (1797, 81),
                 "casern": (1797, 211),
                 "fortress": (1797, 341),
                 "forge": (1797, 471),
                 "turent": (1797, 601),
                 "workshop": (1797, 731),
                 "dragonlair": (1797, 876)}
        self.all_buttons = pygame.sprite.Group()
        for i in image:
            Button(self.all_buttons, i, image[i], "панель справа")

    def get_event(self, event):
        for button in self.all_buttons:
            if event.type == pygame.MOUSEMOTION:
                button.get_anim(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button.rect.collidepoint(event.pos):
                    return button.name

    def draw(self, screen):
        screen.blit(self.panel, (0, 0))
        self.all_buttons.draw(screen)
