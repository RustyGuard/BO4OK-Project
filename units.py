import math
from random import randint
from typing import Dict, Tuple

import pygame
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface

from constants import *

# States

# типы действий рабочих
STATE_DIG = 0
STATE_FIGHT = 1
STATE_BUILD = 2
STATE_CHOP = 3
STATE_ANY_WORK = 4

# типы действий
TARGET_MOVE = 0
TARGET_ATTACK = 1
TARGET_NONE = 2

# типы любых спрайтов в игре - строение,снаряд,воин,декорайция,строение предоставляющее ресурсы
TYPE_BUILDING = 0
TYPE_PROJECTILE = 1
TYPE_FIGHTER = 2
TYPE_RESOURCE = 3

team_id = [
    'black', 'aqua', 'blue', 'green', 'light_green', 'orange', 'pink', 'purple', 'red', 'yellow',
]  # значения цветов игрока в соответсвии с его номером


class Unit(Sprite):  # родительский класс любого воина,существа или строения
    game = None
    free_id = None
    power_cost = 0  # количество места которое занимает юнит(далее "мясо",подробнее в классе Фермы)
    unit_type = TYPE_BUILDING  # стандартное значение
    required_level = 0

    def __init__(self, x, y, id, player_id):
        self.id = id
        self.player_id = player_id
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.x = float(x)
        self.y = float(y)
        self.offsetx = 0  # координаты, учитывающие положение камеры
        self.offsety = 0
        self.can_upgraded = False
        self.level = -1
        self.max_health = UNIT_STATS[type(self)][0] * Forge.get_mult(self)[0]
        self.health = self.max_health
        super().__init__()

    def __str__(self):
        return f'class{type(self)} x{self.x} y{self.y}'

    def is_alive(self):
        return self.health > 0

    def move(self, x, y, game):
        if x != 0:
            self.x += x
            self.rect.centerx = int(self.x) + self.offsetx
            for spr in game.get_building_intersect(self):
                if spr != self:
                    if x < 0:
                        self.rect.left = spr.rect.right
                    else:
                        self.rect.right = spr.rect.left
                    self.x = self.rect.centerx - self.offsetx
                    break
            if self.x < -WORLD_SIZE // 2:
                self.x = -WORLD_SIZE // 2
                self.rect.centerx = int(self.x) + self.offsetx
            if self.x > WORLD_SIZE // 2:
                self.x = WORLD_SIZE // 2
                self.rect.centerx = int(self.x) + self.offsetx

        if y != 0:
            self.y += y
            self.rect.centery = int(self.y) + self.offsety
            for spr in game.get_building_intersect(self):
                if spr != self:
                    if y < 0:
                        self.rect.top = spr.rect.bottom
                    else:
                        self.rect.bottom = spr.rect.top
                    self.y = self.rect.centery - self.offsety
                    break
                if self.y < -WORLD_SIZE // 2:
                    self.y = -WORLD_SIZE // 2
                    self.rect.centery = int(self.y) + self.offsety
                if self.y > WORLD_SIZE // 2:
                    self.y = WORLD_SIZE // 2
                    self.rect.centery = int(self.y) + self.offsety

    def set_offset(self, x, y):  # поправка на положение камеры
        self.offsetx, self.offsety = x, y
        self.update_rect()

    def update_rect(self):
        self.rect.centerx = int(self.x) + self.offsetx
        self.rect.centery = int(self.y) + self.offsety

    def update_image(self):
        pass

    def get_args(self):
        return ''

    def __getitem__(self, item):
        if item == 0:
            return self.x
        if item == 1:
            return self.y
        raise Exception('Noooooo way!!!')

    def get_update_args(self, arr):  # получение данных из массива,для отправки на сервер
        arr.append(str(get_class_id(type(self))))
        arr.append(str(int(self.x)))
        arr.append(str(int(self.y)))
        arr.append(str(self.id))
        arr.append(str(self.player_id))
        arr.append(str(self.health))
        arr.append(str(self.max_health))
        arr.append(str(self.level))
        return arr

    def set_update_args(self, arr, game):  # запись данных в массив,для отправки на сервер
        arr.pop(0)
        self.x = float(arr.pop(0))
        self.y = float(arr.pop(0))
        self.id = int(arr.pop(0))
        self.player_id = int(arr.pop(0))
        self.health = float(arr.pop(0))
        self.max_health = float(arr.pop(0))
        self.level = int(arr.pop(0))

    def send_updated(self, game):  # отправлнение данных серверу
        game.server.send_all('9_' + '_'.join(self.get_update_args([])))

    def take_damage(self, dmg, game):  # получение урона
        self.health -= dmg
        game.server.send_all(f'5_{self.id}_{self.health}_{self.max_health}')

    def next_level(self, game):
        raise Exception('Not supported')

    def level_cost(self, game):
        raise Exception('Not supported')

    def can_be_upgraded(self, game):
        return False

    def kill(self):
        if Unit.free_id is not None:
            Unit.free_id.append(self.id)
            print('id', self.id, 'free now')
        super().kill()


class TwistUnit(Unit):  # подкласс Unit имеющий угол вращения
    def __init__(self, x, y, id, player_id, default_image):
        self.angle = 0
        self.default_image = default_image
        super().__init__(x, y, id, player_id)

    def set_angle(self, angle):
        self.angle = angle
        self.validate_angle()
        self.update_image()

    def add_angle(self, angle):
        self.angle += angle
        self.validate_angle()
        self.update_image()

    def validate_angle(self):  # проверка на возможный угол вращения
        while self.angle >= 360:
            self.angle -= 360
        while self.angle < 0:
            self.angle += 360

    def update_image(self):
        rotated_image = pygame.transform.rotate(self.default_image, -self.angle)
        self.image = rotated_image

    def move_to_angle(self, speed, game):
        self.move(math.cos(math.radians(self.angle)) * speed, math.sin(math.radians(self.angle)) * speed, game)

    def get_update_args(self, arr):
        super().get_update_args(arr)
        arr.append(str(self.angle))
        return arr

    def set_update_args(self, arr, game):
        super().set_update_args(arr, game)
        self.set_angle(int(arr.pop(0)))


class Mine(Unit):  # Шахта,здание располагющее золотом,которое могут добыть рабочие
    placeable = False  # шахту нельзя поставить вручную, они появляются в начале игры
    name = 'Шахта'
    mine = pygame.image.load('sprite-games/building/mine/mine.png')
    image = mine
    required_level = 1
    unit_type = TYPE_RESOURCE  # тип юнитов хранящих ресурсы для добычи

    def __init__(self, x, y, id, player_id):
        self.image = Mine.mine
        super().__init__(x, y, id, player_id)
        self.max_health = UNIT_STATS[type(self)][0]
        self.health = self.max_health

    def update(self, event, game):
        if event.type == SERVER_EVENT_UPDATE:  # убивает спрайт,если объект разрушен или убит
            if not self.is_alive():
                game.kill(self)


class Arrow(TwistUnit):  # Стрела
    image = pygame.image.load(f'sprite-games/warrior/archer/arrow.png')
    name = 'Arrow'
    placeable = False  # объект нельзя поставить вручную,лишь может быть создан другим юнитом
    unit_type = TYPE_PROJECTILE  # Projectile - тип снаряда в игре

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, Arrow.image)
        self.set_angle(int(angle))
        self.time = 300  # максимальное время "жизни" объекта, по истечении которого он пропадает
        self.damage = UNIT_STATS[Arrow][1] * Forge.get_mult(self)[1]

    def update(self, event, game):
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(3, game)
            if event.type == SERVER_EVENT_UPDATE:
                # убивает спрайт стрелы при вылете за экран
                if self.x < -WORLD_SIZE // 2 or self.x > WORLD_SIZE // 2 or self.y < -WORLD_SIZE // 2 or self.y > WORLD_SIZE // 2:
                    game.kill(self)
                    return

                self.time -= 1
                if self.time <= 0:  # убивает спрайт стрелы если кончилось время
                    game.kill(self)
                for spr in game.get_intersect(self):
                    # проверяет то что атакуемый объект - не дружественный юнит и не снаряд
                    if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                        spr.take_damage(self.damage, game)
                        game.kill(self)
                        return

    def get_args(self):
        return f'_{self.angle}'

    def move(self, x, y, game):
        if x != 0:
            self.x += x
        if y != 0:
            self.y += y
        self.update_rect()


class BallistaArrow(TwistUnit):  # Болт баллисты
    image = pygame.image.load(f'sprite-games/warrior/ballista/anim/arrow.png')
    name = 'BallistaArrow'
    placeable = False
    unit_type = TYPE_PROJECTILE

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, BallistaArrow.image)
        self.set_angle(int(angle))
        self.time = 1200
        self.live_time = 5  # "прочность" болта,может задеть только 5 юнитов,после чего спрайт исчезает
        self.striken = []  # список задетых снарядом юнитов,болт не ударит дважды по тому же обьъекту
        self.damage = UNIT_STATS[BallistaArrow][1] * Forge.get_mult(self)[1]

    def update(self, event, game):
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(3, game)
            if event.type == SERVER_EVENT_UPDATE:
                if self.x < -WORLD_SIZE // 2 or self.x > WORLD_SIZE // 2 or self.y < -WORLD_SIZE // 2 or self.y > WORLD_SIZE // 2:
                    game.kill(self)
                    return

                self.time -= 1
                if self.time <= 0:
                    game.kill(self)
                for spr in game.get_intersect(self):
                    if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                        if spr not in self.striken:
                            self.live_time -= (1 if type(spr) != Dragon else 5)  # дракон ломает болт с одного попадания
                            spr.take_damage(self.damage, game)
                            self.striken.append(spr)
                            if self.live_time <= 0:
                                game.kill(self)
                                return

    def get_args(self):
        return f'_{self.angle}'

    def move(self, x, y, game):
        if x != 0:
            self.x += x
        if y != 0:
            self.y += y
        self.update_rect()


class Fighter(TwistUnit):  # надкласс юнитов способных наносить урон и стрелять/добывать ресурсы
    power_cost = 0

    def __init__(self, x, y, id, player_id, default_image):
        super().__init__(x, y, id, player_id, default_image)
        self.target_angle = 0
        self.target = (TARGET_NONE, None)
        self.delay = 0
        self.delay_time = 120  # время задержки,чем ниже тем чаще атакует
        self.damage = UNIT_STATS[type(self)][1] * Forge.get_mult(self)[1]

    def move_to_point(self, event, game, straight_speed, turn_speed, twist_speed=1):
        if event.type == SERVER_EVENT_UPDATE:
            xr = self.target[1][0] - self.x
            yr = self.target[1][1] - self.y
            if math.sqrt(xr * xr + yr * yr) < 40:
                self.set_target(TARGET_NONE, None, game)
                return
        self.find_target_angle()
        if self.turn_around(twist_speed):
            self.move_to_angle(straight_speed, game)
        else:
            self.move_to_angle(turn_speed, game)

    def set_target(self, target_type, coord, game=None):  # задает цель атаки
        self.target = (target_type, coord)
        if game is None:
            return
        if target_type == TARGET_ATTACK:
            game.server.send_all(f'2_{TARGET_ATTACK}_{self.id}_{self.target[1].id}')
        elif target_type == TARGET_NONE:
            game.server.send_all(f'2_{TARGET_NONE}_{self.id}')
        elif target_type == TARGET_MOVE:
            game.server.send_all(f'2_{TARGET_MOVE}_{self.id}_{coord[0]}_{coord[1]}')

    def find_target_angle(self):  # находит угол между целью и объектом для поворота
        self.target_angle = int(
            math.degrees(math.atan2(self.target[1][1] - self.y, self.target[1][0] - self.x)))
        if self.target_angle < 0:
            self.target_angle += 360

    def find_new_target(self, game, radius=1500):  # ищет новую цель в определенном радиусе
        area = Sprite()
        area.rect = Rect(0, 0, radius, radius)
        area.rect.center = self.rect.center
        current = None
        for spr in game.get_intersect(area):
            if spr != self and self.is_valid_enemy(spr):
                if current is None:
                    current = (spr, math.sqrt((spr.x - self.x) ** 2 + (spr.y - self.y) ** 2))
                else:
                    dist = math.sqrt((spr.x - self.x) ** 2 + (spr.y - self.y) ** 2)
                    if dist < current[1]:
                        current = (spr, dist)
        if current:
            self.set_target(TARGET_ATTACK, current[0], game)
            return True
        return False

    def is_valid_enemy(self, enemy):  # проверяет что цель не является снарядом или дружественным юнитом
        return enemy.player_id not in [-1, self.player_id] and enemy.unit_type != TYPE_PROJECTILE

    def turn_around(self, speed=1):  # поворот объекта с определенной скоростью
        angle_diff = self.target_angle - self.angle
        if angle_diff == 0:
            return True
        speed = min(speed, abs(angle_diff))
        if angle_diff < 0:
            if abs(angle_diff) >= 180:
                self.add_angle(speed)
            else:
                self.add_angle(-speed)
        elif angle_diff > 0:
            if abs(angle_diff) >= 180:
                self.add_angle(-speed)
            else:
                self.add_angle(speed)
        return False

    def single_attack(self, game, damage=None):  # атака по цели
        if self.delay <= 0:
            self.target[1].take_damage(self.damage if damage is None else damage, game)
            self.delay += self.delay_time
            return True
        return False

    def throw_projectile(self, game, clazz, spread=0):  # Функция стрельбы.Spread отвечает за разброс
        if self.delay <= 0:
            self.delay += self.delay_time
            game.place(clazz, int(self.x), int(self.y), self.player_id, int(self.angle + randint(-spread, spread)),
                       ignore_space=True, ignore_money=True, ignore_fort_level=True)

    def update_delay(self):
        if self.delay > 0:
            self.delay -= 1

    def close_to_attack(self, distance=1):  # проверяет наличие цели в пределах атаки
        return 2 * abs(self.target[1][0] - self.x) <= self.rect.width + self.target[1].rect.width + distance \
               and 2 * abs(self.target[1][1] - self.y) <= self.rect.height + self.target[1].rect.height + distance

    def get_update_args(self, arr):
        super().get_update_args(arr)
        arr.append(str(self.target[0]))
        if self.target[0] == TARGET_MOVE:
            arr.append(str(self.target[1][0]))
            arr.append(str(self.target[1][1]))
        elif self.target[0] == TARGET_ATTACK:
            arr.append(str(self.target[1].id))
        return arr

    def set_update_args(self, arr, game):
        super().set_update_args(arr, game)
        target = int(arr.pop(0))
        second = None
        arr.append(str(self.target[0]))
        if target == TARGET_MOVE:
            second = int(arr.pop(0)), int(arr.pop(0))
        elif target == TARGET_ATTACK:
            second = game.find_with_id(int(arr.pop(0)))
        self.target = (target, second)

    def kill(self):
        if Unit.game is not None:
            Unit.game.players[self.player_id].power -= self.power_cost
        super().kill()


class Archer(Fighter):  # Лучник, атакующий юнит дальнего и среднего боя
    cost = (100.0, 3.0)  # стоимость создания.Первый аргумент-золото,второй-дерево
    placeable = False  # лучника нельзя поставить,можно создать только в казарме
    name = 'Лучник'
    power_cost = 2  # todo Баланс
    images = []  # список с лучниками всех цветов,в инициализации выбирается цвет игрока
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/archer/{team_id[i]}.png'))
    image = images[0]
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Archer.images[player_id]  # выбор цвета

        super().__init__(x, y, id, player_id, Archer.images[player_id])
        self.delay_time = 60

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.move_to_point(event, game, 1, 0.5, 3)

            elif self.target[0] == TARGET_ATTACK:
                # если цель не жива,то цель обнуляется
                if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, game)
                    return

                self.find_target_angle()
                if event.type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack(1000)
                if self.turn_around(3):
                    if near:
                        if event.type == SERVER_EVENT_UPDATE:
                            # если лучник повернут,а цель рядом,то выпускается стрела
                            self.throw_projectile(game, Arrow)
                    else:
                        self.move_to_angle(1, game)
                elif not near:
                    self.move_to_angle(0.5, game)

            elif self.target[0] == TARGET_NONE:  # если цели нет-находится новая
                if event.type == SERVER_EVENT_UPDATE:
                    self.find_new_target(game)

        elif event.type in [CLIENT_EVENT_SEC, SERVER_EVENT_SEC]:
            pass


class Soldier(Fighter):  # Воин,атакующий юнит ближнего боя
    cost = (100.0, 0.0)
    name = 'Воин'
    placeable = False
    power_cost = 1  # todo Баланс
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/soldier/{team_id[i]}.png'))
    image = images[0]
    required_level = 0
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Soldier.images[player_id]

        super().__init__(x, y, id, player_id, Soldier.images[player_id])

    def update(self, event, game):
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:

            if self.target[0] == TARGET_MOVE:
                self.move_to_point(event, game, 1.5, 1, 2)
                return

            if self.target[0] == TARGET_ATTACK:
                if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, game)
                    return

                self.find_target_angle()
                if event.type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack()
                if self.turn_around(2):
                    if near:
                        if event.type == SERVER_EVENT_UPDATE:
                            # если противник рядом,а воин повернут,то воин наносит ему урон
                            self.single_attack(game)
                    else:
                        self.move_to_angle(1, game)
                elif not near:
                    self.move_to_angle(0.5, game)

            elif self.target[0] == TARGET_NONE:
                if event.type == SERVER_EVENT_UPDATE:
                    self.find_new_target(game)

        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return

    def is_valid_enemy(self, enemy):
        # воин не может атаковать дракона,т.к. воин-класс ближнего боя
        return super().is_valid_enemy(enemy) and type(enemy) != Dragon


class Worker(Fighter):  # Рабочий,добывает золото и дерево,строит здания,носит ресурсы к крепости
    cost = (25.0, 0.0)
    name = 'Рабочий'
    placeable = False
    power_cost = 1  # todo Баланс
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/working/{team_id[i]}.png'))
    image = images[0]
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Worker.images[player_id]

        super().__init__(x, y, id, player_id, Worker.images[player_id])
        self.money = 0  # число золота у рабочего с собой
        self.wood = 0  # число дерева у рабочего с собой
        self.capacity = 25  # вместимость рабочего(не понесет больше 25 ресурсов)
        self.state = STATE_ANY_WORK
        self.delay_time = 60

    def take_damage(self, dmg, game):
        super().take_damage(dmg, game)
        self.state = STATE_FIGHT
        self.find_new_target(game, 2000)

    def update(self, event, game):
        if event.type not in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            return

        if self.target[0] == TARGET_MOVE:
            self.move_to_point(event, game, 1.5, 1)
            return

        elif self.target[0] == TARGET_ATTACK:
            if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                self.set_target(TARGET_NONE, None, game)
                if self.state == STATE_FIGHT:
                    self.state = STATE_ANY_WORK
                return

            self.find_target_angle()
            if event.type == SERVER_EVENT_UPDATE:
                self.update_delay()
            near = self.close_to_attack()
            if self.turn_around(2):
                if near:
                    if event.type == SERVER_EVENT_UPDATE:
                        if isinstance(self.target[1], Mine):
                            if self.single_attack(game):
                                # если рабочий рядом с шахтой,то он забирает золото,если может унести
                                self.money += MONEY_PER_PUNCH
                                if self.is_full():
                                    self.find_new_target(game, 3000)
                                    return
                        elif isinstance(self.target[1], Tree):
                            if self.single_attack(game):
                                # если рабочий рядом с деревом,то он забирает древесину,если может унести
                                self.wood += WOOD_PER_PUNCH
                                if self.is_full():
                                    self.find_new_target(game, 3000)
                                    return
                        elif isinstance(self.target[1], UncompletedBuilding):
                            # если рабочий рядом с неготовым зданием,то он строит его
                            if (self.single_attack(game, -5)) and \
                                    (self.target[1].health >= self.target[1].max_health) and \
                                    (not self.find_new_target(game, 3000)):
                                self.set_target(TARGET_NONE, None)
                                return
                        elif isinstance(self.target[1], Fortress) and self.player_id == self.target[1].player_id:
                            # если рабочий рядом с крепостью,то он отдает ей ресурсы
                            game.give_resources(self.player_id, (self.money, self.wood))
                            self.wood = self.money = 0
                            self.find_new_target(game, 3000)
                            return
                        else:
                            self.single_attack(game)
                else:
                    self.move_to_angle(1.5, game)
            elif not near:
                self.move_to_angle(1, game)

        elif self.target[0] == TARGET_NONE:
            if event.type == SERVER_EVENT_UPDATE:
                self.find_new_target(game, 3000)

        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return

    def is_full(self):
        return self.money + self.wood >= self.capacity

    def is_valid_enemy(self, enemy):
        # выбирает цель рабочему,взависимости от заданной деятельности
        if self.is_full():
            return isinstance(enemy, Fortress) and enemy.player_id == self.player_id
        if self.state == STATE_ANY_WORK:
            return isinstance(enemy, (Mine, Tree, UncompletedBuilding)) and enemy.player_id in [-1, self.player_id]
        if self.state == STATE_DIG:
            return isinstance(enemy, Mine)
        elif self.state == STATE_CHOP:
            return isinstance(enemy, Tree)
        elif self.state == STATE_BUILD:
            return isinstance(enemy, UncompletedBuilding)
        elif self.state == STATE_FIGHT:
            return super().is_valid_enemy(enemy) and not isinstance(enemy, Dragon)


class ProductingBuild(Unit):  # Надкласс зданий производящих юнитов(например, казарма)
    def __init__(self, x, y, id, player_id, delay, valid_types):
        self.time = delay
        self.delay = delay
        self.units_tray = []  # очередь производимых юнитов
        self.valid_types = valid_types  # возможные к производству типы юнитов
        super().__init__(x, y, id, player_id)

    def add_to_queque(self, clazz, game):  # добавление юнита в очередь
        if clazz in self.valid_types:
            if game.claim_unit_cost(self.player_id, clazz):
                self.units_tray.append(clazz)

    def create_unit(self, game, clazz):  # расположение юнита
        if clazz is not None:
            if game.place(clazz,
                          int(self.x) - randint(self.rect.width // 2 + 25, self.rect.width + self.rect.width // 2),
                          int(self.y) - randint(-50, 50),
                          self.player_id, ignore_space=True, ignore_money=True, ignore_fort_level=True) is not None:
                game.safe_send(self.player_id, '3_6')

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return
        if event.type == SERVER_EVENT_SEC and self.time > 0 and self.units_tray:
            self.time -= 1
        elif self.time == 0:  # с определенной задержкой создает юнита, имитирую тренировку
            self.time = self.delay
            self.create_unit(game, self.units_tray.pop(0))


class Fortress(ProductingBuild):  # Крепость, задает уровень игрока,делает рабочих - ключевое здание в игре
    name = 'Крепость'
    placeable = True
    cost = (250.0, 50.0)

    level_costs = [(300.0, 50.0, 0), (400.0, 100.0, 0)]  # todo Баланс
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/fortress/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    instances = []

    @staticmethod
    def get_player_level(player_id):
        # получает уровень игрока,это необходимо,т.к. наиболее улучешнная крепость влияет на остальные
        max_level = 0
        to_remove = []
        for inst in Fortress.instances:
            if not inst.is_alive():
                to_remove.append(inst)
                continue
            if inst.player_id == player_id and inst.level > max_level:
                max_level = inst.level
        for i in to_remove:
            Fortress.instances.remove(i)
        return max_level

    def __init__(self, x, y, id, player_id):
        self.image = Fortress.images[player_id]
        super().__init__(x, y, id, player_id, 2, [Worker])
        self.level = 0
        self.can_upgraded = True
        Fortress.instances.append(self)

    def update(self, event, game):
        super().update(event, game)
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return

    def next_level(self, game):
        if self.level == 3:
            print('Already on max level!')
            return
        self.level += 1

    def level_cost(self, game):
        if self.level == 3:
            print('Max level!')
            return None
        return Fortress.level_costs[self.level - 1]

    def can_be_upgraded(self, game):
        return 3 > self.level >= 0


class Forge(Unit):  # Кузня,несколько уровней.При постройке,умножает "статы" юнитов на соответсвующий коэффициент
    name = 'Кузня'
    placeable = True
    cost = (200.0, 50.0)

    level_costs = [(300.0, 75.0, 0), (400.0, 125.0, 0), (500.0, 150.0, 0)]  # todo Баланс
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/forge/{team_id[i]}.png'))
    image = images[0]
    required_level = 2  # Можно построить только со второго уровня крепости
    unit_type = TYPE_BUILDING

    @staticmethod
    def get_mult(unit):  # получает множитель остальных кузней
        if Unit.game is None:
            return 1.0, 1.0
        if unit.unit_type in [TYPE_RESOURCE]:
            return 1.0, 1.0
        if unit.player_id not in Unit.game.players:
            return 1.0, 1.0
        player = Unit.game.players[unit.player_id]
        player_forge_level = player.max_forge_level
        health_mult = 1.0
        damage_mult = 1.0
        if unit.unit_type == TYPE_PROJECTILE:
            if player_forge_level == 2:
                damage_mult *= K_DAMAGE_UP
        if unit.unit_type == TYPE_FIGHTER:
            if player_forge_level == 1:
                health_mult *= K_HP_UP
            elif player_forge_level == 2:
                damage_mult *= K_DAMAGE_UP
        if unit.unit_type == TYPE_BUILDING:
            if not isinstance(unit, UncompletedBuilding):
                if player_forge_level == 3:
                    health_mult *= K_BUILDHP_UP
                elif player_forge_level == 4:
                    health_mult *= K_BUILDHP_UP2
        return health_mult, damage_mult

    def __init__(self, x, y, id, player_id):
        self.image = Forge.images[player_id]
        super().__init__(x, y, id, player_id)
        self.level = 0
        self.can_upgraded = True

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return

    def next_level(self, game):
        if self.level == 4:
            print('Already on max level!')
            return
        self.level += 1
        if game.players[self.player_id].max_forge_level < self.level:
            game.players[self.player_id].max_forge_level = self.level

        for obj in game.sprites:
            if obj.player_id == self.player_id:
                h_mult, d_mult = Forge.get_mult(obj)
                if h_mult != 1.0:
                    obj.health *= h_mult
                    obj.max_health *= h_mult
                    game.server.send_all(f'5_{obj.id}_{obj.health}_{obj.max_health}')
                if d_mult != 1.0:
                    obj.damage *= d_mult

    def level_cost(self, game):
        if self.level == 4:
            print('Max level!')
            return None
        return Forge.level_costs[self.level - 1]

    def can_be_upgraded(self, game):
        return 4 > self.level >= 0


class Casern(ProductingBuild):  # подкласс ProductingBuild, производящий лучников,солдат
    placeable = True
    name = 'Казарма'
    cost = (100.0, 25.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/casern/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = Casern.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Archer, Soldier])


class DragonLore(ProductingBuild):  # подкласс ProductingBuild, производящий только Драконов
    placeable = True
    name = 'Драконье логово'
    cost = (500.0, 0.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/dragonlair/{team_id[i]}.png'))
    image = images[0]
    required_level = 3
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = DragonLore.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Dragon])


class Workshop(ProductingBuild):  # подкласс ProductingBuild, производящий только баллисты
    placeable = True
    name = 'Мастерская'
    cost = (350.0, 100.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/workshop/{team_id[i]}.png'))
    image = images[0]
    required_level = 2
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = Workshop.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Ballista])


class MagicBall(TwistUnit):  # Магический шар,снаряд, выпускаемый третьим уровнем башни лучников
    image = pygame.image.load(f'sprite-games/building/turret/3/magic_ball.png')
    name = 'Magic Ball'
    placeable = False
    unit_type = TYPE_PROJECTILE

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, MagicBall.image)
        self.set_angle(int(angle))
        self.time = 300
        self.interact_timer = 15
        self.interacted = False
        self.damage = UNIT_STATS[MagicBall][1] * Forge.get_mult(self)[1]

    def update(self, event, game):
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(1.5, game)
            if event.type == SERVER_EVENT_UPDATE:
                if self.x < -WORLD_SIZE // 2 or self.x > WORLD_SIZE // 2 or self.y < -WORLD_SIZE // 2 or self.y > WORLD_SIZE // 2:
                    game.kill(self)
                    return

                self.time -= 1
                if self.time <= 0:
                    game.kill(self)

                if not self.interacted:
                    for spr in game.get_intersect(self):
                        if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                            self.interacted = True
                            return

                if self.interacted:
                    self.interact_timer -= 1
                    if self.interact_timer <= 0:
                        for spr in game.get_intersect(self):
                            if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                                spr.take_damage(UNIT_STATS[type(self)][1], game)
                        game.kill(self)
                        return

    def get_args(self):
        return f'_{self.angle}'

    def move(self, x, y, game):
        if x != 0:
            self.x += x
        if y != 0:
            self.y += y
        self.update_rect()


class ArcherTower(Fighter):  # Башня лучников,имеет три уровня,оборонительное сооружение
    cost = (200.0, 20.0)
    placeable = True
    name = 'Башня'
    level_costs = [(30.0, 30.0, 0), (40.0, 40.0, 0), (70.0, 50.0, 0)]  # todo Баланс
    images = [[pygame.image.load(f'sprite-games/building/turret/{team_id[i]}.png') for i in range(10)],
              [pygame.image.load(f'sprite-games/building/turret/2/{team_id[i]}.png') for i in range(10)],
              [pygame.image.load(f'sprite-games/building/turret/3/{team_id[i]}.png') for i in range(10)]]
    # разные спрайты для разных уровней
    image = images[0][0]
    required_level = 1
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.archer_image = Archer.images[player_id]
        self.player_id = player_id
        super().__init__(x, y, id, player_id, ArcherTower.images[1][player_id])
        self.level = 0
        self.can_upgraded = True
        self.update_image()

    def update_image(self):
        self.image = Surface(ArcherTower.images[self.level - 1][self.player_id].get_rect().size, pygame.SRCALPHA)
        self.image.blit(ArcherTower.images[self.level - 1][self.player_id], (0, 0))
        # не отрисовывает лучника поверх башни, если она не первого уровня
        if self.level == 1:
            self.image.blit(pygame.transform.rotate(self.archer_image, -self.angle), (10, 10))

    def next_level(self, game):
        if self.level == 3:
            print('Already on max level!')
            return
        self.level += 1
        self.levels_update()

    def levels_update(self):
        # башня второго уровня стреляет быстрее,а третьего медленнее,но магическими снарядами
        if self.level == 2:
            self.delay_time = 20
        elif self.level == 3:
            self.delay_time = 100

    def level_cost(self, game):
        if self.level == 3:
            print('Max level!')
            return None
        return ArcherTower.level_costs[self.level - 1]

    def can_be_upgraded(self, game):
        return 3 > self.level >= 0

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.find_target_angle()
                turned = self.turn_around(3)

                if event.type == SERVER_EVENT_UPDATE:
                    if turned:
                        self.set_target(TARGET_NONE, None, game)
                        return

            elif self.target[0] == TARGET_ATTACK:
                if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None)
                    return

                self.find_target_angle()
                if event.type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                if self.turn_around(3):
                    if event.type == SERVER_EVENT_UPDATE:
                        # тип снаряда
                        if self.level != 3:
                            self.throw_projectile(game, Arrow)
                        else:
                            self.throw_projectile(game, MagicBall)

            elif self.target[0] == TARGET_NONE:
                if event.type == SERVER_EVENT_UPDATE:
                    self.find_new_target(game)


class Tree(Unit):  # Дерево, из него рабочие добывают древесину
    placeable = False
    name = 'Дерево'
    tree = pygame.image.load('sprite-games/icon/tree.png')
    image = tree
    required_level = 1
    unit_type = TYPE_RESOURCE

    def __init__(self, x, y, id, player_id):
        self.image = Tree.tree
        super().__init__(x, y, id, player_id)
        self.max_health = UNIT_STATS[type(self)][0]
        self.health = self.max_health

    def update(self, event, game):
        if event.type == SERVER_EVENT_UPDATE:
            if not self.is_alive():
                game.kill(self)


class FireProjectile(TwistUnit):  # Снаряд выпускаемый драконом
    images = []
    for i in range(1, 7):
        images.append(pygame.image.load(f'sprite-games/warrior/dragon/Flame/{i}.png'))
    name = 'Пламень'
    placeable = False
    unit_type = TYPE_PROJECTILE

    def __init__(self, x, y, id, player_id, angle):
        self.time = 0
        self.current_state = 0
        self.set_angle(int(angle))
        super().__init__(x, y, id, player_id, None)
        self.angle = int(angle)
        self.damage = UNIT_STATS[type(self)][1] * Forge.get_mult(self)[1]

    def update(self, event, game):
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.time += 1
            if self.time >= 15:
                self.time = 0
                self.current_state += 1
                if event.type == CLIENT_EVENT_UPDATE:
                    self.current_state = min(5, self.current_state)
                    self.update_image()
                elif event.type == SERVER_EVENT_UPDATE:
                    if self.current_state == 6:
                        game.kill(self)
                        print('Dead')
                        return
                    for spr in game.get_intersect(self):
                        if (spr != self) and (spr.unit_type != TYPE_PROJECTILE) \
                                and (spr.player_id not in [self.player_id, -1]) and not isinstance(spr, Dragon):
                            spr.take_damage(self.damage, game)

    def get_args(self):
        print(self.angle)
        return f'_{self.angle}'

    def update_image(self):
        rotated_image = pygame.transform.rotate(FireProjectile.images[self.current_state], -self.angle)
        self.image = rotated_image


class Dragon(Fighter):  # Дракон,уникальный воин,может быть ранен только снарядами
    cost = (300.0, 0.0)
    power_cost = 5  # todo Баланс
    name = 'Дракон'
    placeable = False
    images = []
    for i in range(10):
        anim = (
            pygame.image.load(f'sprite-games/warrior/dragon/{team_id[i]}.png'),
            pygame.image.load(f'sprite-games/warrior/dragon/anim/{team_id[i]}.png')
        )
        images.append(anim)
    image = images[0][0]
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.time = 0
        # параметры смены анимации полета дракона
        self.anim_switch = 0
        self.anim_tuple = Dragon.images[player_id]

        super().__init__(x, y, id, player_id, Soldier.images[player_id])
        self.update_image()
        self.delay = 45 * 10

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return
        if event.type == CLIENT_EVENT_UPDATE:
            self.time += 1
            if self.time >= 45:
                self.anim_switch = (self.anim_switch + 1) % 2
                self.time = 0
                self.update_image()

        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:

            if self.target[0] == TARGET_MOVE:
                self.move_to_point(event, game, 1, 0.5)
                return

            elif self.target[0] == TARGET_ATTACK:
                if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, game)
                    return

                self.find_target_angle()
                if event.type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack()
                if self.turn_around(2):
                    if near:
                        if event.type == SERVER_EVENT_UPDATE:
                            self.throw_projectile(game, FireProjectile)
                    else:
                        self.move_to_angle(1, game)
                elif not near:
                    self.move_to_angle(0.5, game)

            elif self.target[0] == TARGET_NONE:
                if event.type == SERVER_EVENT_UPDATE:
                    self.find_new_target(game)

    def update_image(self):
        rotated_image = pygame.transform.rotate(self.anim_tuple[self.anim_switch], -self.angle)
        self.image = rotated_image


class UncompletedBuilding(Unit):  # класс,не построенного,но уже размещенного здания
    placeable = False
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id, clazz_id):
        self.clazz = UNIT_TYPES[int(clazz_id)]
        self.image = UNIT_TYPES[int(clazz_id)].image
        super().__init__(x, y, id, player_id)
        self.health = 1
        self.max_health = 100
        self.completed = False

    def update(self, event, game):
        # если здание закончено,то спрайт UncompletedBuilding исчезает, а на его месте появлется его построенный аналог
        if event.type == SERVER_EVENT_UPDATE:
            if not self.is_alive():
                game.kill(self)
                return
            if self.health >= self.max_health:
                game.place(self.clazz, int(self.x), int(self.y), self.player_id,
                           ignore_space=True, ignore_money=True, ignore_fort_level=True)
                self.completed = True
                game.safe_send(self.player_id, '3_5')
                game.kill(self)

    def get_args(self):
        return f'_{get_class_id(self.clazz)}'

    def take_damage(self, dmg, game):
        if not self.completed:
            super().take_damage(dmg, game)

    def is_alive(self):
        return super().is_alive() and not self.completed


class Ballista(Fighter):  # Баллиста,уникальный класс воина,имеет преимущество против драконов
    cost = (300.0, 50.0)
    placeable = False
    power_cost = 5  # todo Баланс
    name = 'Баллиста'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/ballista/{team_id[i]}.png'))
    image = images[0]
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Ballista.images[player_id]
        super().__init__(x, y, id, player_id, Ballista.images[player_id])
        self.delay_time = 400

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return
        if event.type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.move_to_point(event, game, 1, 0.5, 1)

            elif self.target[0] == TARGET_ATTACK:
                if event.type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, game)
                    return

                self.find_target_angle()
                if event.type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack(1500)
                if self.turn_around(3):
                    if near:
                        if event.type == SERVER_EVENT_UPDATE:
                            # стреляет вышеупомянутыми болтами, а не стрелами
                            self.throw_projectile(game, BallistaArrow)
                    else:
                        self.move_to_angle(1, game)
                elif not near:
                    self.move_to_angle(0.5, game)

            elif self.target[0] == TARGET_NONE:
                if event.type == SERVER_EVENT_UPDATE:
                    self.find_new_target(game)


class Farm(Unit):  # Ферма, чем их больше,тем больше уровень "мяса" и больше юнитов может позволить себе игрок
    name = 'Ферма'
    placeable = True
    cost = (50.0, 10.0)

    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/farm/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    instances = []

    @staticmethod
    def get_player_meat(player_id):  # получение уровня "мяса" игрока.Отвечает за возможное число юнитов
        meat = 10
        to_remove = []
        for inst in Farm.instances:
            if not inst.is_alive():
                to_remove.append(inst)
                continue
            if inst.player_id == player_id:
                meat += 10
        for i in to_remove:
            Farm.instances.remove(i)
        return meat

    def __init__(self, x, y, id, player_id):
        self.image = Farm.images[player_id]
        super().__init__(x, y, id, player_id)
        Farm.instances.append(self)

    def update(self, event, game):
        if not self.is_alive():
            if event.type == SERVER_EVENT_UPDATE:
                game.kill(self)
                return


# Словарь типов возможных юнитов
UNIT_TYPES = {
    0: Soldier,
    1: Mine,
    2: Archer,
    3: Arrow,
    4: Casern,
    5: Fortress,
    6: Worker,
    7: ArcherTower,
    8: Tree,
    9: Dragon,
    10: FireProjectile,
    11: UncompletedBuilding,
    12: Ballista,
    13: BallistaArrow,
    14: DragonLore,
    15: Workshop,
    16: Forge,
    17: Farm,
    18: MagicBall
}
# 'Статы' всех юнитов - максимальное здоровье и урон
UNIT_STATS = {  # (max_health, base_dmg)
    Worker: (500, 5),  # Worker,
    Soldier: (150, 50),  # Soldier,
    Archer: (100, 0),  # Archer,
    Ballista: (400, 0),  # Ballista,
    Dragon: (600, 0),  # Dragon,
    Mine: (10000, 0),  # Mine,
    Arrow: (1, 60),  # Arrow,
    Casern: (400, 0),  # Casern,
    Fortress: (2000, 0),  # Fortress,
    ArcherTower: (500, 0),  # ArcherTower,
    Tree: (30, 0),  # Tree,
    FireProjectile: (1, 50),  # FireProjectile,
    UncompletedBuilding: (200, 0),  # UncompletedBuilding,
    BallistaArrow: (1, 300),  # BallistaArrow,
    DragonLore: (1000, 0),  # DragonLore,
    Workshop: (1200, 0),  # Workshop,
    Forge: (500, 0),  # Forge
    Farm: (250, 0),  # Farm
    MagicBall: (1, 120)  # Magic Ball
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
