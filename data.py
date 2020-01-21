import pygame, sqlite3, datetime
from client import ClientWait

# инициализация глобальный перемен функций
cursor = pygame.image.load('sprite-games/menu/cursor.png')
FPS = 60
clock = pygame.time.Clock()
nicname = ""


class Button(pygame.sprite.Sprite):
    """ Класс универсальной кнопки """

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
        """ Функция обработки анимации и нажатия кнопки """
        if event.type == pygame.MOUSEMOTION:  # Анимация кнопки
            if not self.f:
                if self.rect.collidepoint(event.pos):
                    self.image = self.anim
                else:
                    if self.image == self.anim:
                        self.image = self.stok_image
        if event.type == pygame.MOUSEBUTTONDOWN:  # функция нажатия на кнопку
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    return [self.name, nicname]


def read_settings():
    """ Функция чтения файла с настройками """
    set = open('settings.txt', 'r')
    settings = {}
    for i in set.read().split("\n"):
        a = i.split()
        if a[1] == "TRUE":
            settings[a[0]] = True
        elif a[1] == "FALSE":
            settings[a[0]] = False
        else:
            try:
                settings[a[0]] = int(a[1])
            except ValueError:
                settings[a[0]] = a[1]
    set.close()
    return settings


def write_settings(settings):
    """ Функция записи измененения настронек """
    wr = []
    set = open('settings.txt', 'w+')
    for i in settings:
        if settings[i] is True:
            wr.append(i + " TRUE")
        elif settings[i] is False:
            wr.append(i + " FALSE")
        else:
            wr.append(i + " " + str(settings[i]))
    set.seek(0)
    set.write("\n".join(wr))
    set.close()


def menu(screen):
    """ Функция окна гланого меню """
    global cursor, FPS, clock
    background = pygame.image.load('sprite-games/menu/background.png').convert()
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
        screen.blit(background, (0, 0))
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def headpiece(screen):
    """ Функция заставки создателей """
    global clock

    # инициализация изображений
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
    pygame.mixer.music.load('9.mp3')
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(0.2)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return
        if Bo4ok_rect[0] < 232:
            Bo4ok_rect[0] += 4.4
            Potick1_rect[0] += 4.4
        else:
            Potick1 = Potick2
            Bo4ok_rect[0] = 410
            Potick1_rect[0] = 910
            if not f:
                Timer += 1
                if Timer > 48:
                    f = True
                    Timer = 0
            if Timer > 140:
                pygame.mixer.music.stop()
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
        clock.tick(30)


def ip(screen, musik):
    """ Функция окна подключения к игре по айпи """
    global cursor, FPS, clock, nicname
    background = pygame.image.load('sprite-games/play/ip основа.png')
    screen.blit(background, (0, 0))
    image = {"OK": (1085, 709),
             "back_menu": (558, 709)}

    way = "play"
    ip = "192.168.0."

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
                            musik.stop()
                            gameover(screen, ClientWait().play(screen, ip if ip != '' else 'localhost', nick=nicname))
                            musik.play(-1)
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
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def play(screen):
    """ Функция мерню подключеия/создания сессии """
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
    """ функция окна настроек """
    global cursor, FPS, clock
    background = pygame.image.load('sprite-games/settings/background.png')
    screen.blit(background, (0, 0))
    fon = pygame.image.load('sprite-games/settings/fon.png')
    camera = pygame.image.load('sprite-games/settings/camera.png')
    tick_field_image = {"BACKGROUND": (15, 183),
                        "CAMERA": (15, 315)}
    way = "settings"
    settings = read_settings()  # чтение существующих настроек

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
                    write_settings(settings)
                    return ["back_menu", nicname]
            for button in all_buttons:
                if button.get_event(event):
                    write_settings(settings)
                    return button.get_event(event)
            for tick_field in all_tick_field:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if tick_field.rect.collidepoint(event.pos):  # изменение состояния определённой настройки
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
    """ Функция титров с создателями и проделанной работой """
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
        i2_rect[1] -= 2
        i3_rect[1] -= 2
        pygame.display.flip()
        clock.tick(FPS)


def write_statistics(stats):
    """ Функция записи статистики в .db файл """
    statistics = sqlite3.connect("statistics.db")
    a = "', '".join([str(stats[i]) for i in stats])
    statistics.execute(
        f"INSERT INTO stats({', '.join([i for i in stats])}, datetime) VALUES('{a}', '{datetime.datetime.today().strftime('%Y/%m/%d %H:%M')}')")
    statistics.commit()
    statistics.close()


def statistics(screen):
    """ Функция окна со стотистикой пользователя """
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
                    if n + 15 < len(res):
                        n += 1
                if str(event).split()[5][0] == "4":
                    if n > 0:
                        n -= 1
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        for y, result in enumerate(res[n:n + 15]):
            for x, i in enumerate(result[1:]):
                screen.blit(font.render(i, 1, (255, 255, 255)), (50 + 212 * x, 180 + 57 * y))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def gameover(screen, game):
    """ Функция окончания игры """
    write_statistics(game[1])  # запись статитстики
    global clock

    # инициализация изображений
    sword = pygame.image.load('sprite-games/over/sword.png')
    sword1 = pygame.image.load('sprite-games/over/swords.png')
    if game[0]:
        win = pygame.image.load('sprite-games/over/win.png')
    else:
        win = pygame.image.load('sprite-games/over/loose.png')

    f = False
    coords = [[-2000, 0], [-2000, 2000], [0, 2000], [2000, 2000], [2000, 0], [2000, -2000], [0, -2000], [-2000, -2000]]

    pygame.mixer.music.load('9.mp3')
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(0.2)
    n = 0
    k = 1
    timer = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return

        screen.fill(pygame.Color("black"))
        if f:
            flip = pygame.transform.rotate(sword1, n)
            rot_rect = flip.get_rect(center=(960, 540))
            n += 1 * k // 1
            screen.blit(flip, rot_rect)
            screen.blit(win, win.get_rect(center=(960, 540)))
            k += 0.2
            timer += 1
            if timer == 210:
                pygame.mixer.music.stop()
                return
        else:
            for n, i in enumerate(coords):
                cor = []
                for j in i:
                    if j < -100:
                        cor.append(j + 25)
                    elif j > 100:
                        cor.append(j - 25)
                    else:
                        cor.append(j)
                if cor[0] == -100 and cor[1] == 100:
                    f = True
                coords[n] = cor
            for n, i in enumerate(coords):
                flip = pygame.transform.rotate(sword, (n + 1 // 2) * 45)
                rot_rect = flip.get_rect(center=(960 + i[0], 540 + i[1]))
                screen.blit(flip, rot_rect)
        pygame.display.flip()
        clock.tick(30)
