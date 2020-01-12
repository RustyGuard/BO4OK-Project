import math
from random import randint

import pygame
from pygame import Color
from pygame.rect import Rect
from pygame.sprite import Sprite
from constants import SERVER_EVENT_SEC, SERVER_EVENT_UPDATE, CLIENT_EVENT_SEC, CLIENT_EVENT_UPDATE

# States
STATE_DIG = 0
STATE_FIGHT = 1
STATE_BUILD = 2
STATE_CHOP = 3

TARGET_MOVE = 0
TARGET_ATTACK = 1
TARGET_NONE = 2

team_id = [
    'black', 'aqua', 'blue', 'green', 'light_green', 'orange', 'pink', 'purple', 'red', 'yellow',
]


class Unit(Sprite):

    def __init__(self, x, y, id, player_id):
        self.id = id
        self.player_id = player_id
        self.rect = self.image.get_rect()  # Init image before
        self.rect.centerx = x
        self.rect.centery = y
        self.x = float(x)
        self.y = float(y)
        self.offsetx = 0
        self.offsety = 0
        self.has_target = False
        self.max_health = 100
        self.health = 100
        self.live = True
        self.is_building = True
        self.is_projectile = False
        super().__init__()

    def is_alive(self):
        return self.live and self.health > 0

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

    def set_offset(self, x, y):
        self.offsetx, self.offsety = x, y
        self.update_rect()

    def update_rect(self):
        self.rect.centerx = int(self.x) + self.offsetx
        self.rect.centery = int(self.y) + self.offsety

    def get_args(self):
        return ''

    def __getitem__(self, item):
        if item == 0:
            return self.x
        if item == 1:
            return self.y
        raise Exception('Noooooo way!!!')

    def get_update_args(self, arr):
        arr.append(str(get_class_id(type(self))))
        arr.append(str(int(self.x)))
        arr.append(str(int(self.y)))
        arr.append(str(self.id))
        arr.append(str(self.player_id))
        arr.append(str(self.health))
        return arr

    def set_update_args(self, arr, game):
        arr.pop(0)
        self.x = float(arr.pop(0))
        self.y = float(arr.pop(0))
        self.id = int(arr.pop(0))
        self.player_id = int(arr.pop(0))
        self.health = float(arr.pop(0))

    def send_updated(self, game):
        game.server.send_all('9_' + '_'.join(self.get_update_args([])))

    def take_damage(self, dmg, game):
        self.health -= dmg
        game.server.send_all(f'5_{self.id}_{self.health}_{self.max_health}')


class TwistUnit(Unit):
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

    def validate_angle(self):
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


class Mine(Unit):
    placeable = False
    name = 'Mine'
    mine = pygame.image.load('sprite-games/building/mine/mine.png')
    image = mine
    required_level = 1

    def __init__(self, x, y, id, player_id):
        self.image = Mine.mine
        super().__init__(x, y, id, player_id)
        self.max_health = 1000
        self.health = self.max_health

    def update(self, *args):
        if args[0].type == SERVER_EVENT_UPDATE:
            if not self.is_alive():
                args[1].kill(self)


class Arrow(TwistUnit):
    image = pygame.image.load(f'sprite-games/warrior/archer/arrow.png')
    damage = 5
    name = 'Arrow'
    placeable = False

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, Arrow.image)
        self.set_angle(int(angle))
        self.is_projectile = True
        self.is_building = False
        self.time = 1200

    def update(self, *args):
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(3, args[1])
            if args[0].type == SERVER_EVENT_UPDATE:
                self.time -= 1
                if self.time <= 0:
                    args[1].kill(self)
                for spr in args[1].get_intersect(self):
                    if spr.player_id != -1 and spr != self and spr.player_id != self.player_id and not spr.is_projectile:
                        spr.take_damage(Arrow.damage, args[1])
                        args[1].kill(self)
                        return

    def get_args(self):
        return f'_{self.angle}'

    def move(self, x, y, game):
        if x != 0:
            self.x += x
        if y != 0:
            self.y += y
        self.update_rect()


class Fighter(TwistUnit):
    def __init__(self, x, y, id, player_id, default_image):
        super().__init__(x, y, id, player_id, default_image)
        self.target_angle = 0
        self.target = (TARGET_NONE, None)
        self.has_target = True
        self.is_building = False
        self.delay = 0
        self.delay_time = 120
        self.damage = 10

    def set_target(self, target_type, coord):
        # print(f'Entity[{self.id}] found a new target of [{target_type}] is [{coord}]')
        self.target = (target_type, coord)

    def find_target_angle(self):
        self.target_angle = int(
            math.degrees(math.atan2(self.target[1][1] - self.y, self.target[1][0] - self.x)))
        if self.target_angle < 0:
            self.target_angle += 360

    def find_new_target(self, game, radius=1500):
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
            self.set_target(TARGET_ATTACK, current[0])
            game.server.send_all(f'2_{TARGET_ATTACK}_{self.id}_{current[0].id}')
            return True
        return False

    def is_valid_enemy(self, enemy):
        return enemy.player_id != -1 and enemy.player_id != self.player_id and not enemy.is_projectile

    def turn_around(self, speed=1):
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

    def single_attack(self, game):
        if self.delay <= 0:
            self.target[1].take_damage(self.damage, game)
            self.delay += self.delay_time
            return True
        return False

    def throw_projectile(self, game, clazz):
        if self.delay <= 0:
            self.delay += self.delay_time
            game.place(clazz, int(self.x), int(self.y), self.player_id, int(self.angle),
                       ignore_space=True, ignore_money=True, ignore_fort_level=True)

    def mass_attack(self, game):
        pass

    def update_delay(self):
        if self.delay > 0:
            self.delay -= 1

    def close_to_attack(self, distance=1):
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


class Archer(Fighter):
    cost = (1.0, 1.0)
    placeable = False
    name = 'Лучник'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/archer/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed

    def __init__(self, x, y, id, player_id):
        self.image = Archer.images[player_id]

        super().__init__(x, y, id, player_id, Archer.images[player_id])

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    xr = self.target[1][0] - self.x
                    yr = self.target[1][1] - self.y
                    if math.sqrt(xr * xr + yr * yr) < 40:
                        args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                        self.set_target(TARGET_NONE, None)
                        return
                self.find_target_angle()
                if self.turn_around(3):
                    self.move_to_angle(1, args[1])
                else:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                    self.set_target(TARGET_NONE, None)
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack(1000)
                if self.turn_around(3):
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            self.throw_projectile(args[1], Arrow)
                    else:
                        self.move_to_angle(1, args[1])
                elif not near:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])

        elif args[0].type in [CLIENT_EVENT_SEC, SERVER_EVENT_SEC]:
            pass


class Soldier(Fighter):
    cost = (5.0, 0.0)
    name = 'Воин'
    placeable = False
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/soldier/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed

    def __init__(self, x, y, id, player_id):
        self.image = Soldier.images[player_id]

        super().__init__(x, y, id, player_id, Soldier.images[player_id])

    def update(self, *args):
        if not args:
            return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    xr = self.target[1][0] - self.x
                    yr = self.target[1][1] - self.y
                    if math.sqrt(xr * xr + yr * yr) < 40:
                        args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                        self.set_target(TARGET_NONE, None)
                        return
                self.find_target_angle()
                if self.turn_around(2):
                    self.move_to_angle(1, args[1])
                else:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                    self.set_target(TARGET_NONE, None)
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack()
                if self.turn_around(2):
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            self.single_attack(args[1])
                    else:
                        self.move_to_angle(1, args[1])
                elif not near:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])

        elif args[0].type in [CLIENT_EVENT_SEC, SERVER_EVENT_SEC]:
            pass
            # print('En', self.id, self.x, self.y)

        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return


class Worker(Fighter):
    cost = (5.0, 0.0)
    name = 'Рабочий'
    placeable = False
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/working/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed

    def __init__(self, x, y, id, player_id):
        self.image = Worker.images[player_id]

        super().__init__(x, y, id, player_id, Worker.images[player_id])
        self.damage = 1
        self.money = 0
        self.wood = 0
        self.capacity = 50
        self.state = STATE_DIG

    def take_damage(self, dmg, game):
        super().take_damage(dmg, game)
        self.state = STATE_FIGHT
        self.find_new_target(game, 2000)

    def update(self, *args):
        if not args:
            return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    xr = self.target[1][0] - self.x
                    yr = self.target[1][1] - self.y
                    if math.sqrt(xr * xr + yr * yr) < 40:
                        args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                        self.set_target(TARGET_NONE, None)
                        return
                self.find_target_angle()
                if self.turn_around():
                    self.move_to_angle(1, args[1])
                else:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                    self.set_target(TARGET_NONE, None)
                    self.state = STATE_DIG
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack()
                if self.turn_around():
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            if type(self.target[1]) == Mine:
                                if self.single_attack(args[1]):
                                    self.money += 10
                                    if self.money >= self.capacity:
                                        self.money = self.capacity
                                        self.find_new_target(args[1], 3000)
                                        return
                            elif type(self.target[1]) == Fortress and self.player_id == self.target[1].player_id:
                                args[1].players[self.player_id].money += self.money
                                self.money = 0
                                self.find_new_target(args[1], 3000)
                                return
                            else:
                                self.single_attack(args[1])
                    else:
                        self.move_to_angle(1, args[1])
                elif not near:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    print('NONE')
                    self.find_new_target(args[1], 3000)

        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return

    def is_full(self):
        return self.money * 0.5 + self.wood > 25

    def is_valid_enemy(self, enemy):
        if self.is_full():
            return type(enemy) == Fortress and enemy.player_id == self.player_id
        if self.state == STATE_DIG:
            return type(enemy) == Mine
        # elif self.state == STATE_CHOP:
        # return type(enemy) == Tree
        elif self.state == STATE_FIGHT:
            return super().is_valid_enemy(enemy)


class ProductingBuild(Unit):
    def __init__(self, x, y, id, player_id, delay, valid_types):
        self.time = delay
        self.delay = delay
        self.units_tray = []  # для примера
        self.valid_types = valid_types
        super().__init__(x, y, id, player_id)

    def add_to_queque(self, clazz):
        if clazz in self.valid_types:
            self.units_tray.append(clazz)

    def create_unit(self, game, clazz):
        if clazz is not None:
            game.place(clazz, int(self.x) - randint(self.rect.width // 2 + 25, self.rect.width + self.rect.width // 2),
                       int(self.y) - randint(-50, 50),
                       self.player_id, ignore_space=True, ignore_money=False, ignore_fort_level=True)

    def update(self, *args):
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type == SERVER_EVENT_SEC and self.time > 0 and self.units_tray:
            self.time -= 1
        elif self.time == 0:
            self.time = self.delay
            self.create_unit(args[1], self.units_tray.pop(0))


class Fortress(ProductingBuild):
    name = 'Крепость'
    placeable = True
    cost = (1.0, 0.0)
    levels_info = [(150.0, True, False, False), (200.0, True, True, False), (300.0, True, True, True)]
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/fortress/{team_id[i]}.png'))
    image = images[0]
    required_level = 1

    instances = []

    @staticmethod
    def get_player_level(player_id):
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
        self.level = 1
        self.workers_tray = 0
        super().__init__(x, y, id, player_id, 2, [Worker])
        Fortress.instances.append(self)

    def update(self, *args):
        super().update(*args)
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return


class Casern(ProductingBuild):
    placeable = True
    name = 'Казарма'
    cost = (1.0, 0.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/casern/{team_id[i]}.png'))
    image = images[0]
    required_level = 1

    def __init__(self, x, y, id, player_id):
        self.image = Casern.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Archer, Soldier])


class ArcherTower(Fighter):
    cost = (1.0, 1.0)
    placeable = True
    name = 'Башня'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/turret/{team_id[i]}.png'))
    image = images[0]
    required_level = 1

    def __init__(self, x, y, id, player_id):
        self.image = ArcherTower.images[player_id]
        self.archer_image = Archer.images[player_id]

        super().__init__(x, y, id, player_id, ArcherTower.images[player_id])

    def update_image(self):

        rotated_archer = pygame.transform.rotate(self.archer_image, -self.angle)
        self.image.blit(rotated_archer, (13, 13))

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    xr = self.target[1][0] - self.x
                    yr = self.target[1][1] - self.y
                    if math.sqrt(xr * xr + yr * yr) < 40:
                        args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                        self.set_target(TARGET_NONE, None)
                        return
                self.find_target_angle()

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    args[1].server.send_all(f'2_{TARGET_NONE}_{self.id}')
                    self.set_target(TARGET_NONE, None)
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack(1000)
                if self.turn_around(3):
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            self.throw_projectile(args[1], Arrow)

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])

        elif args[0].type in [CLIENT_EVENT_SEC, SERVER_EVENT_SEC]:
            pass


UNIT_TYPES = {
    0: Soldier,
    1: Mine,
    2: Archer,
    3: Arrow,
    4: Casern,
    5: Fortress,
    6: Worker,
    7: ArcherTower
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
