﻿import pygame
import sqlite3
import datetime

# инициализация глобальный перемен функций
cursor = pygame.image.load('sprite/icon/cursor.png')
clock = pygame.time.Clock()
nickname = ""  # никнейм игрока(если поле пустое - выберает рандомное имя)
ip_conect = "192.168.0."  # айпи подключения к желаемому хосту


class Button(pygame.sprite.Sprite):
    """ Класс универсальной кнопки """

    def __init__(self, group, name, image, button_type=None):
        super().__init__(group)
        if not button_type:  # стандартная кнопка
            self.stok_image = pygame.image.load(f'sprite/buttons/{name}.png')
            self.anim = pygame.image.load(f'sprite/buttons/anim/{name}.png')
        elif button_type == 1:  # нопка с постаянно включенной анимацией
            self.stok_image = self.anim = pygame.image.load(f'sprite/buttons/anim/{name}.png')
        elif button_type == 2:  # булевое окно(вкл, выкл)
            self.stok_image = pygame.image.load(f'sprite/buttons/field.png')
            self.anim = pygame.image.load(f'sprite/buttons/tick_field.png')
        elif button_type == 3:  # нопка с постаянно выключенной анимацией
            self.stok_image = self.anim = pygame.image.load(f'sprite/buttons/{name}.png')
        self.name = name  # имя кнопки
        self.image = self.stok_image  # стандартное изображение
        self.rect = self.image.get_rect()
        self.rect.topleft = image
        self.button_type = button_type  # тип кнопки

    def get_event(self, event):
        """ Функция обработки анимации и нажатия кнопки """
        if event.type == pygame.MOUSEMOTION:  # Анимация кнопки
            if self.button_type != 2:
                if self.rect.collidepoint(event.pos):
                    self.image = self.anim
                else:
                    if self.image == self.anim:
                        self.image = self.stok_image
        if event.type == pygame.MOUSEBUTTONDOWN:  # функция нажатия на кнопку
            if event.button == 1:
                if self.rect.collidepoint(event.pos):  # если произошло нажатие - возвращает имякнопки
                    return self.name


class Music:
    """ Класс с работой с аудиофайлайми """

    def __init__(self, window, sounds):
        if window == "menu":
            pygame.mixer.music.load('music/menu.ogg')
        self.window = window
        self.sounds = {}
        for i in sounds:
            self.sounds[i] = pygame.mixer.Sound(f'music/{i}.ogg')
        self.set_musik_volume()

    def set_musik_volume(self, volume=None):
        """ Функция обработки изменения громокость """
        if not volume:
            volume = float(read_settings()["VOLUME"])
        if self.window == "menu":
            pygame.mixer.music.set_volume(volume)
        for i in self.sounds:
            self.sounds[i].set_volume(volume)

    def all_stop(self):
        """ Функция выключения всей музыки """
        if self.window == "menu":
            pygame.mixer.music.pause()
        for i in self.sounds:
            self.sounds[i].stop()

    def game_sounds_play(self):
        """ Функция включения всей музыки """
        pygame.mixer.music.pause()
        for i in self.sounds:
            self.sounds[i].play(-1)
        self.set_musik_volume()

    def update(self, name_window):
        """ Функция перелючения музыки музыки """
        self.all_stop()
        if name_window in ["headpiece", "creators"]:
            self.sounds[name_window].play(-1)
        else:
            pygame.mixer.music.unpause()
        self.set_musik_volume()


def read_settings(filename='settings/settings.txt'):
    """ Функция чтения файла с настройками """
    settings = {}
    for i in open(filename, 'r').read().split("\n"):
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
    return settings


def write_settings(settings):
    """ Функция записи измененений настронек """
    new_settings = []
    file_settings = open('settings/settings.txt', 'w+')
    for i in settings:
        if settings[i] is True:
            new_settings.append(i + " TRUE")
        elif settings[i] is False:
            new_settings.append(i + " FALSE")
        else:
            new_settings.append(i + " " + str(settings[i]))
    file_settings.seek(0)
    file_settings.write("\n".join(new_settings))
    file_settings.close()


def menu(screen):
    """ Функция окна гланого меню """
    global cursor, clock
    background = pygame.image.load('sprite/data/menu.png').convert()
    screen.blit(background, (0, 0))

    image = {"play": (28, 950),
             "settings": (400, 950),
             "statistics": (772, 950),
             "creators": (1145, 950),
             "exit": (1590, 950)}

    all_buttons = pygame.sprite.Group()
    for i in image:
        Button(all_buttons, i, image[i])

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
        clock.tick(60)


def headpiece(screen):
    """ Функция заставки создателей """
    global clock

    # инициализация изображений
    bo4ok = pygame.image.load('sprite/headpiece/Bo4ok.png')
    games = pygame.image.load('sprite/headpiece/Games.png')
    potick = pygame.image.load('sprite/headpiece/Potick1.png')
    potick2 = pygame.image.load('sprite/headpiece/Potick2.png')
    stone = pygame.image.load('sprite/headpiece/Stone.png')
    water = pygame.image.load('sprite/headpiece/Water.png')

    bo4ok_rect = [-900, 500]
    potick_rect = [-400, 500]
    timer = 0
    water_condition = False
    suffering = float(read_settings()["SUFFERING"])  # если FALSE, то добавляет возможность скипа заставки :D
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if not suffering:
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
        if bo4ok_rect[0] < 232:  # Движение надписи "bo4ok potick"
            bo4ok_rect[0] += 4.4
            potick_rect[0] += 4.4
        else:  # как тольуо напись врезается в камень, потик измениет изображение
            potick = potick2
            bo4ok_rect[0] = 410
            potick_rect[0] = 910
            if not water_condition:
                timer += 1
                if timer > 48:
                    water_condition = True  # через определённый промежуток времени вытекает вода
                    timer = 0
            else:
                if timer > 140:  # задержка после вытекания воды, перед выключением анимации
                    pygame.mixer.music.stop()
                    return "menu"
                else:
                    timer += 1
        screen.fill(pygame.Color("white"))
        screen.blit(stone, (1170, 500))
        screen.blit(bo4ok, bo4ok_rect)
        screen.blit(potick, potick_rect)
        screen.blit(games, (1350, 500))
        if water_condition:
            screen.blit(water, (990, 558))
        pygame.display.flip()
        clock.tick(30)


def ip(screen):
    """ Функция окна подключения к игре по айпи """
    global cursor, clock, ip_conect
    background = pygame.image.load('sprite/data/ip.png').convert()
    screen.blit(background, (0, 0))

    image = {"OK": (1085, 709),
             "menu": (558, 709)}

    all_buttons = pygame.sprite.Group()
    for i in image:
        Button(all_buttons, i, image[i])

    font = pygame.font.Font("font/NK57.ttf", 100)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["play", ip_conect]
            for button in all_buttons:
                if button.get_event(event):
                    if button.name == "OK":
                        return ["OK", ip_conect]
                    return ["play", ip_conect]
            if event.type == pygame.KEYDOWN:
                if (event.unicode == "." and ip_conect.count(".") < 3) or \
                        (event.unicode in "1234567890" and len(ip_conect.split(".")[-1]) < 3):
                    ip_conect += event.unicode
                if event.key == pygame.K_BACKSPACE:
                    ip_conect = ip_conect[:-1]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(ip_conect, 1, (255, 255, 255)), (565, 460))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(60)


def play(screen):
    """ Функция мерню подключеия/создания сессии """
    global cursor, clock, nickname
    background = pygame.image.load('sprite/data/play.png').convert()
    screen.blit(background, (0, 0))

    image = {"host": (330, 250),
             "connect": (330, 455),
             "menu": (340, 700)}

    all_buttons = pygame.sprite.Group()
    for n, i in enumerate(image):
        Button(all_buttons, i, image[i])

    font = pygame.font.Font("font/NK57.ttf", 55)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return ["menu", nickname]
            for button in all_buttons:
                if button.get_event(event):
                    return [button.get_event(event), nickname]
            if event.type == pygame.KEYDOWN:
                if event.unicode in "ёйцукенгшщзхъфывапролджэячсмить" \
                                    "бюqwertyuiopasdfghjklzxcvbnm1234567890 _-":
                    if len(nickname) < 11:
                        nickname += event.unicode
                if event.key == pygame.K_BACKSPACE:
                    nickname = nickname[:-1]
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        screen.blit(font.render(nickname, 1, (255, 255, 255)), (810, 745))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(60)


def settings(screen, music):
    """ функция окна настроек """
    global cursor, clock
    background = pygame.image.load('sprite/data/settings.png').convert()
    screen.blit(background, (0, 0))

    tick_field_image = {"BACKGROUND": (15, 183),
                        "CAMERA": (15, 315),
                        "FPS": (15, 447),
                        "DEBUG": (15, 579),
                        "PARTICLES": (15, 711)}
    settings = read_settings()  # чтение существующих настроек

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "menu", (12, 12))

    all_volume_cursor = pygame.sprite.Group()
    Button(all_volume_cursor, "volume_cursor", (float(settings["VOLUME"]) * 664 + 98, 953))

    all_tick_field = pygame.sprite.Group()  # окошки с галочками
    for i in tick_field_image:
        Button(all_tick_field, i, tick_field_image[i], 2)

    flag_volume_cursor = False  # ечли True, то полунок громкости - двигается
    volume_cursor_x = 0  # позиция ползунка громкости во время нажатия на ползунок
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    write_settings(settings)
                    return "menu"
            if flag_volume_cursor:  # движение ползунка громкости
                mouse_x_coords = pygame.mouse.get_pos()[0]
                # значение переменной координаты мыши присвоено до цикла, да бы не инициализировать много раз
                for volume_cursor in all_volume_cursor:
                    if 98 <= volume_cursor_x + mouse_x_coords <= 762:
                        volume_cursor.rect.x = volume_cursor_x + pygame.mouse.get_pos()[0]
                    if 98 > volume_cursor_x + mouse_x_coords:
                        volume_cursor.rect.x = 98
                    if 762 < volume_cursor_x + mouse_x_coords:
                        volume_cursor.rect.x = 762
                    music.set_musik_volume((volume_cursor.rect.x - 98) / 664)
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
                        # запоминаем позицию ползунка в моемент нажатия
                        volume_cursor_x = volume_cursor.rect.x - pygame.mouse.get_pos()[0]
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
        clock.tick(60)


def titers(screen):
    """ Функция титров с создателями и проделанной работой """
    global clock
    background = pygame.image.load('sprite/data/titers_fon.png').convert()
    titers = pygame.image.load('sprite/data/titers.png')
    titers_rect = [200, 1200]
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        screen.blit(background, (0, 0))
        screen.blit(titers, titers_rect)
        titers_rect[1] -= 1
        if titers_rect[1] < -4765:
            return "menu"
        pygame.display.flip()
        clock.tick(60)


def write_statistics(stats):
    """ Функция записи статистики в .db файл """
    statistics = sqlite3.connect("data_games/statistics.db")
    a = "', '".join([str(stats[i]) for i in stats])
    statistics.execute(
        f"INSERT INTO stats({', '.join([i for i in stats])}, datetime) "
        f"VALUES('{a}', '{datetime.datetime.today().strftime('%Y/%m/%d %H:%M')}')")
    statistics.commit()
    statistics.close()


def statistics(screen):
    """ Функция окна со стотистикой пользователя """
    global cursor, clock
    background = pygame.image.load('sprite/data/statistics.png').convert()
    screen.blit(background, (0, 0))

    all_buttons = pygame.sprite.Group()
    Button(all_buttons, "menu", (12, 12))

    stats = sqlite3.connect("data_games/statistics.db").cursor().execute("SELECT * FROM stats").fetchall()

    font = pygame.font.Font("font/NK57.ttf", 61)
    line_position = 0
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
                    if line_position + 14 < len(stats):
                        line_position += 1
                if str(event).split()[5][0] == "4":
                    if line_position > 0:
                        line_position -= 1
        screen.blit(background, (0, 0))
        all_buttons.draw(screen)
        for y, line in enumerate(stats[::-1][line_position:line_position + 14]):
            for x, value in enumerate(line[1:]):
                screen.blit(font.render(value, 1, (255, 255, 255)), (52 + 212 * x, 228 + 57 * y))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
        pygame.display.flip()
        clock.tick(60)


def gameover(screen, game_result):
    """ Функция анимации окончания игры """
    write_statistics(game_result[1])  # запись статитстики
    global clock

    # инициализация изображений и музыки
    sword = pygame.image.load('sprite/over/sword.png')
    swords = pygame.image.load('sprite/over/swords.png')
    if game_result[0]:
        win = pygame.image.load('sprite/over/win.png')
        sound = pygame.mixer.Sound("music/win.ogg")
    else:
        win = pygame.image.load('sprite/over/loose.png')
        sound = pygame.mixer.Sound("music/loose.ogg")
    blackout = pygame.image.load('sprite/data/blackout.png')
    sound.set_volume(float(read_settings()["VOLUME"]))
    sound.play(-1)

    animation_of_whirling = False
    coords_sword = [[-1000, 0], [-1000, 1000], [0, 1000],
                    [1000, 1000], [1000, 0], [1000, -1000],
                    [0, -1000], [-1000, -1000]]

    angle_of_inclination = 0  # переменная угла поворота мечей
    timer = 0

    game_result[2].draw(screen)
    screen.blit(blackout, (0, 0))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    sound.stop()
                    return "menu"

        if animation_of_whirling:  # кручение мечей
            angle_of_inclination += 0.5
            flip = pygame.transform.rotate(swords, angle_of_inclination)
            screen.blit(flip, flip.get_rect(center=(960, 540)))
            screen.blit(win, win.get_rect(center=(960, 540)))
            timer += 1
            if timer == 300:
                sound.stop()
                return "menu"

        else:  # сближение мечей к центру
            for number, coords in enumerate(coords_sword):
                new_coords = []
                for j in coords:
                    if j < -110:
                        new_coords.append(j + 5)
                    elif j > 110:
                        new_coords.append(j - 5)
                    else:
                        new_coords.append(j)
                if new_coords[0] == -110 and new_coords[1] == 110:  # проверка на максимальное сближение
                    animation_of_whirling = True
                coords_sword[number] = new_coords
            for n, i in enumerate(coords_sword):
                flip = pygame.transform.rotate(sword, (n + 1 // 2) * 45)
                screen.blit(flip, flip.get_rect(center=(960 + i[0], 540 + i[1])))
        pygame.display.flip()
        clock.tick(60)
