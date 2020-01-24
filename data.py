import pygame, sqlite3, datetime

# инициализация глобальный перемен функций
cursor = pygame.image.load('sprite-games/menu/cursor.png')
FPS = 60
clock = pygame.time.Clock()
nicname = ""
ip_a = "192.168.0."


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
                    return self.name


class Music:
    def __init__(self):
        pygame.mixer.music.load('music/menu.ogg')
        self.sounds = {}
        for i in ["creators", "build_a_farm", "click", "construction_completed", "eror", "investigation_completed", "headpiece"]:
            self.sounds[i] = pygame.mixer.Sound(f'music/{i}.ogg')
        self.set_musik_volume()

    def set_musik_volume(self):
        volume = float(read_settings()["VOLUME"])
        pygame.mixer.music.set_volume(volume)
        for i in self.sounds:
            self.sounds[i].set_volume(volume)

    def all_stop(self):
        pygame.mixer.music.pause()
        for i in self.sounds:
            self.sounds[i].stop()

    def update(self, name_window):
        self.all_stop()
        if name_window in ["headpiece", "creators"]:
            self.sounds[name_window].play()
        else:
            pygame.mixer.music.unpause()



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
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
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
                return "menu"
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


def ip(screen):
    """ Функция окна подключения к игре по айпи """
    global cursor, FPS, clock, ip_a
    background = pygame.image.load('sprite-games/play/ip основа.png').convert()
    screen.blit(background, (0, 0))
    image = {"OK": (1085, 709),
             "menu": (558, 709)}

    way = "play"

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
                    return ["play", ip_a]
            for button in all_buttons:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button.rect.collidepoint(event.pos):
                        if button.name == "OK":
                            return ["OK", ip_a]
                        return ["play", ip_a]
                if button.get_event(event):
                    return button.get_event(event)
            if event.type == pygame.KEYDOWN:
                if event.unicode in "1234567890.:":
                    ip_a += event.unicode
                if event.key == 8:
                    ip_a = ip_a[:-1]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(ip_a, 1, (255, 255, 255)), (565, 460))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def play(screen):
    """ Функция мерню подключеия/создания сессии """
    global cursor, FPS, clock, nicname
    background = pygame.image.load('sprite-games/play/Основа1.png').convert()
    screen.blit(background, (0, 0))
    FPS = 60
    image = {"host": (330, 250),
             "connect": (330, 455),
             "menu": (340, 700)}
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
                    return ["menu", nicname]
            for button in all_buttons:
                if button.get_event(event):
                    return [button.get_event(event), nicname]
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
    background = pygame.image.load('sprite-games/settings/background.png').convert()
    screen.blit(background, (0, 0))
    tick_field_image = {"BACKGROUND": (15, 183),
                        "CAMERA": (15, 315),
                        "FPS": (15, 447),
                        "DEBUG": (15, 579),
                        "PARTICLES": (15, 711)}
    way = "settings"
    settings = read_settings()  # чтение существующих настроек

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "menu", (12, 12), way)

    all_volume_cursor = pygame.sprite.Group()
    Button(all_volume_cursor, "volume_cursor", (float(settings["VOLUME"]) * 664 + 98, 953), way)

    all_tick_field = pygame.sprite.Group()
    for i in tick_field_image:
        Button(all_tick_field, i, tick_field_image[i], way, 1)

    flag_volume_cursor = False
    mouse_x = 0
    volume_cursor_x = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    write_settings(settings)
                    return "menu"
            if flag_volume_cursor:
                for volume_cursor in all_volume_cursor:
                    if 98 <= volume_cursor_x - mouse_x + pygame.mouse.get_pos()[0] <= 762:
                        volume_cursor.rect.x = volume_cursor_x - mouse_x + pygame.mouse.get_pos()[0]
                    if 98 > volume_cursor_x - mouse_x + pygame.mouse.get_pos()[0]:
                        volume_cursor.rect.x = 98
                    if 762 < volume_cursor_x - mouse_x + pygame.mouse.get_pos()[0]:
                        volume_cursor.rect.x = 762
                    pygame.mixer.music.set_volume((volume_cursor.rect.x - 98) / 664)
                    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        flag_volume_cursor = False
                        settings["VOLUME"] = (volume_cursor.rect.x - 98) / 664
            else:
                for button in all_buttons:
                    if button.get_event(event):
                        write_settings(settings)
                        return button.get_event(event)
                for volume_cursor in all_volume_cursor:
                    if volume_cursor.get_event(event):
                        flag_volume_cursor = True
                        mouse_x = pygame.mouse.get_pos()[0]
                        volume_cursor_x = volume_cursor.rect.x
                for tick_field in all_tick_field:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        all_volume_cursor.draw(screen)
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(FPS)


def titers(screen):
    """ Функция титров с создателями и проделанной работой """
    global FPS, clock
    i1 = pygame.image.load('sprite-games/титры/1.png').convert()
    i2 = pygame.image.load('sprite-games/титры/4.png')
    i2_rect = [200, 1080]
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        screen.blit(i1, (0, 0))
        screen.blit(i2, i2_rect)
        i2_rect[1] -= 2
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
    background = pygame.image.load('sprite-games/statistics/background.png').convert()
    screen.blit(background, (0, 0))
    way = "settings"

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "menu", (12, 12), way)

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
                    return "menu"
            for button in all_buttons:
                if button.get_event(event):
                    return button.get_event(event)
            if event.type == pygame.MOUSEBUTTONUP:
                if str(event).split()[5][0] == "5":
                    if n + 14 < len(res):
                        n += 1
                if str(event).split()[5][0] == "4":
                    if n > 0:
                        n -= 1
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        for y, result in enumerate(res[n:n + 15]):
            for x, i in enumerate(result[1:]):
                screen.blit(font.render(i, 1, (255, 255, 255)), (52 + 212 * x, 237 + 57 * y))
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

    n = 0
    k = 1
    timer = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        # for i in sprites:
            # screen.blit(i[0], i[0])
        screen.fill((0, 255, 100))
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
                return "menu"
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
