import pygame, sqlite3, datetime
from client import ClientWait

cursor = pygame.image.load('sprite-games/menu/cursor.png')
FPS = 60
clock = pygame.time.Clock()
nicname = ""


class Button(pygame.sprite.Sprite):
    def __init__(self, group, name, image, way, f=None):
        super().__init__(group)
        if not f:
            self.stok_image = pygame.image.load(f'sprite-games/{way}/{name}.png')
            self.anim = pygame.image.load(f'sprite-games/{way}/anim/{name}.png')
        else:
            self.stok_image = pygame.image.load(f'sprite-games/{way}/field.png')
            self.anim = pygame.image.load(f'sprite-games/{way}/tick_field.png')
        self.name = name
        self.image = self.stok_image
        self.rect = self.image.get_rect()
        self.rect.topleft = image
        self.f = f

    def get_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if not self.f:
                if self.rect.collidepoint(event.pos):
                    self.image = self.anim
                else:
                    if self.image == self.anim:
                        self.image = self.stok_image
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return [self.name, nicname]


def read_settings():
    set = open('settings.txt', 'r')
    settings = {}
    for i in set.read().split("\n"):
        a = i.split()
        if a[1] == "TRUE":
            settings[a[0]] = True
        elif a[1] == "FALSE":
            settings[a[0]] = False
        else:
            settings[a[0]] = a[1]
    set.close()
    return settings


def write_settings(settings):
    wr = []
    set = open('settings.txt', 'w+')
    for i in settings:
        if settings[i] == True:
            wr.append(i + " TRUE")
        elif settings[i] == False:
            wr.append(i + " FALSE")
        else:
            wr.append(i + " " + settings[i])
    set.seek(0)
    set.write("\n".join(wr))
    set.close()


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
            for button in all_buttons:
                if button.get_event(event):
                    return button.get_event(event)
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
    n = 0
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
        # flip = pygame.transform.rotate(Stone, n)
        # rot_rect = flip.get_rect(center=(1272, 566))
        # n += 1
        # screen.blit(flip, rot_rect)
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
             "back_menu": (558, 709)}
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
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["play", nicname]
            for button in all_buttons:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button.rect.collidepoint(event.pos):
                        if button.name == "OK":
                            ClientWait().play(screen, ip if ip != '' else 'localhost', nick=nicname)
                        return ["play", nicname]
                if button.get_event(event):
                    return button.get_event(event)
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
    background = pygame.image.load('sprite-games/play/Основа1.png')
    screen.blit(background, (0, 0))
    FPS = 60
    image = {"host": (330, 250),
             "connect": (330, 455),
             "back_menu": (340, 700)}
    way = "play"

    all_buttons = pygame.sprite.Group()
    for n, i in enumerate(image):
        if n < 3:
            Button(all_buttons, i, image[i], way)
    font = pygame.font.Font(None, 80)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["back_menu", nicname]
            for button in all_buttons:
                if button.get_event(event):
                    return button.get_event(event)
            if event.type == pygame.KEYDOWN:
                if event.unicode in "ёйцукенгшщзхъфывапролджэячсмить" \
                                    "бюqwertyuiopasdfghjklzxcvbnm1234567890" or \
                        event.unicode in "ёйцукенгшщзхъфывапролджэячсми" \
                                         "тьбюqwertyuiopasdfghjklzxcvbnm1234567890".upper():
                    nicname += event.unicode
                if event.key == 8:
                    nicname = nicname[:-1]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(nicname, 1, (255, 255, 255)), (810, 740))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def settings(screen):
    global cursor, FPS, clock
    background = pygame.image.load('sprite-games/settings/background.png')
    screen.blit(background, (0, 0))
    fon = pygame.image.load('sprite-games/settings/fon.png')
    camera = pygame.image.load('sprite-games/settings/camera.png')
    tick_field_image = {"BACKGROUND": (15, 183),
                        "CAMERA": (15, 315)}
    way = "settings"
    settings = read_settings()

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "back_menu", (12, 12), way)

    all_tick_field = pygame.sprite.Group()
    for i in tick_field_image:
        Button(all_tick_field, i, tick_field_image[i], way, 1)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["back_menu", nicname]
            for button in all_buttons:
                if button.get_event(event):
                    return button.get_event(event)
            for tick_field in all_tick_field:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if tick_field.rect.collidepoint(event.pos):
                        if settings[tick_field.name]:
                            settings[tick_field.name] = False
                        else:
                            settings[tick_field.name] = True
        for tick_field in all_tick_field:
            if settings[tick_field.name]:
                tick_field.image = tick_field.anim
            else:
                tick_field.image = tick_field.stok_image
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        all_tick_field.draw(screen)
        screen.blit(fon, (170, 208))
        screen.blit(camera, (170, 340))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def titers(screen):
    global FPS, clock
    i1 = pygame.image.load('sprite-games/титры/1.png')
    i2 = pygame.image.load('sprite-games/титры/2.png')
    i3 = pygame.image.load('sprite-games/титры/3.png')
    i2_rect = [450, 1080]
    i3_rect = [450, 2530]
    sound1 = pygame.mixer.Sound('music/settings.ogg')
    sound1.play()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    sound1.stop()
                    return
        screen.blit(i1, (0, 0))
        screen.blit(i2, i2_rect)
        screen.blit(i3, i3_rect)
        i2_rect[1] -= 0.5
        i3_rect[1] -= 0.5
        pygame.display.flip()
        clock.tick(FPS)


def write_statistics(a, stats):
    statistics = sqlite3.connect("statistics.db")
    statistics.execute(f"INSERT INTO stats({', '.join([i for i in stats])}, datetime) "
                       f"VALUES({', '.join([stats[i] for i in stats])}, "
                       f"{datetime.datetime.today().strftime('%Y/%m/%d %H:%M')})")
    statistics.commit()
    statistics.close()


def statistics(screen):
    global cursor, FPS, clock
    background = pygame.image.load('sprite-games/statistics/background.png')
    screen.blit(background, (0, 0))
    way = "settings"

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "back_menu", (12, 12), way)

    con = sqlite3.connect("statistics.db")
    req = "SELECT * FROM stats"
    cur = con.cursor()
    res = cur.execute(req).fetchall()

    font = pygame.font.Font(None, 80)
    n = 0
    n_max = len(res)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["back_menu", nicname]
            for button in all_buttons:
                if button.get_event(event):
                    return button.get_event(event)
            if event.type == pygame.MOUSEBUTTONUP:
                if str(event).split()[5][0] == "5":
                    if n + 1 < n_max:
                        n += 1
                if str(event).split()[5][0] == "4":
                    if n > 0:
                        n -= 1
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        for y, result in enumerate(res[n:n+15]):
            for x, i in enumerate(result[1:]):
                screen.blit(font.render(i, 1, (255, 255, 255)), (50 + 212 * x, 180 + 57 * y))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)

