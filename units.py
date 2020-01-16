import math
from random import randint

import pygame
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface

from constants import *

# States
STATE_DIG = 0
STATE_FIGHT = 1
STATE_BUILD = 2
STATE_CHOP = 3
STATE_ANY_WORK = 4

TARGET_MOVE = 0
TARGET_ATTACK = 1
TARGET_NONE = 2

TYPE_BUILDING = 0
TYPE_PROJECTILE = 1
TYPE_FIGHTER = 2
TYPE_DECOR = 3
TYPE_RESOURCE = 4

team_id = [
    'black', 'aqua', 'blue', 'green', 'light_green', 'orange', 'pink', 'purple', 'red', 'yellow',
]


class Unit(Sprite):
    game = None

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
        self.can_upgraded = False
        self.level = -1
        self.max_health = UNIT_STATS[type(self)][0] * Forge.get_mult(self)[0]
        self.health = self.max_health
        super().__init__()

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
            if self.x < -5000:
                self.x = -5000
                self.rect.centerx = int(self.x) + self.offsetx
            if self.x > 5000:
                self.x = 5000
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
                if self.y < -5000:
                    self.y = -5000
                    self.rect.centery = int(self.y) + self.offsety
                if self.y > 5000:
                    self.y = 5000
                    self.rect.centery = int(self.y) + self.offsety

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
        arr.append(str(self.max_health))
        arr.append(str(self.level))
        return arr

    def set_update_args(self, arr, game):
        arr.pop(0)
        self.x = float(arr.pop(0))
        self.y = float(arr.pop(0))
        self.id = int(arr.pop(0))
        self.player_id = int(arr.pop(0))
        self.health = float(arr.pop(0))
        self.max_health = float(arr.pop(0))
        self.level = int(arr.pop(0))

    def send_updated(self, game):
        game.server.send_all('9_' + '_'.join(self.get_update_args([])))

    def take_damage(self, dmg, game):
        self.health -= dmg
        game.server.send_all(f'5_{self.id}_{self.health}_{self.max_health}')

    def next_level(self, game):
        raise Exception('Not supported')

    def level_cost(self, game):
        raise Exception('Not supported')

    def can_be_upgraded(self, game):
        return False


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
    name = 'Шахта'
    mine = pygame.image.load('sprite-games/building/mine/mine.png')
    image = mine
    required_level = 1
    unit_type = TYPE_RESOURCE

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
    name = 'Arrow'
    placeable = False
    unit_type = TYPE_PROJECTILE

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, Arrow.image)
        self.set_angle(int(angle))
        self.time = 1200
        self.damage = UNIT_STATS[Arrow][1] * Forge.get_mult(self)[1]

    def update(self, *args):
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(3, args[1])
            if args[0].type == SERVER_EVENT_UPDATE:
                if self.x < -5000 or self.x > 5000 or self.y < -5000 or self.y > 5000:
                    args[1].kill(self)
                    return

                self.time -= 1
                if self.time <= 0:
                    args[1].kill(self)
                for spr in args[1].get_intersect(self):
                    if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                        spr.take_damage(self.damage, args[1])
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


class BallistaArrow(TwistUnit):
    image = pygame.image.load(f'sprite-games/warrior/ballista/anim/arrow.png')
    name = 'BallistaArrow'
    placeable = False
    unit_type = TYPE_PROJECTILE

    def __init__(self, x, y, id, player_id, angle):
        super().__init__(x, y, id, player_id, Arrow.image)
        self.set_angle(int(angle))
        self.time = 1200
        self.live_time = 5
        self.striken = []
        self.damage = UNIT_STATS[BallistaArrow][1] * Forge.get_mult(self)[1]

    def update(self, *args):
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.move_to_angle(3, args[1])
            if args[0].type == SERVER_EVENT_UPDATE:
                if self.x < -5000 or self.x > 5000 or self.y < -5000 or self.y > 5000:
                    args[1].kill(self)
                    return

                self.time -= 1
                if self.time <= 0:
                    args[1].kill(self)
                for spr in args[1].get_intersect(self):
                    if spr.player_id not in [-1, self.player_id] and spr.unit_type != TYPE_PROJECTILE:
                        if spr not in self.striken:
                            self.live_time -= (1 if type(spr) != Dragon else 5)
                            spr.take_damage(self.damage, args[1])
                            self.striken.append(spr)
                            if self.live_time <= 0:
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
    power_cost = 0

    def __init__(self, x, y, id, player_id, default_image):
        super().__init__(x, y, id, player_id, default_image)
        self.target_angle = 0
        self.target = (TARGET_NONE, None)
        self.delay = 0
        self.delay_time = 120
        self.damage = UNIT_STATS[type(self)][1] * Forge.get_mult(self)[1]
        if Unit.game is not None:
            Unit.game.players[self.player_id].power += self.power_cost

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

    def set_target(self, target_type, coord, game=None):
        # print(f'Entity[{self.id}] found a new target of [{target_type}] is [{coord}]')
        self.target = (target_type, coord)
        if game is None:
            return
        if target_type == TARGET_ATTACK:
            game.server.send_all(f'2_{TARGET_ATTACK}_{self.id}_{self.target[1].id}')
        elif target_type == TARGET_NONE:
            game.server.send_all(f'2_{TARGET_NONE}_{self.id}')
        elif target_type == TARGET_MOVE:
            game.server.send_all(f'2_{TARGET_MOVE}_{self.id}_{coord[0]}_{coord[1]}')

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
            self.set_target(TARGET_ATTACK, current[0], game)
            return True
        return False

    def is_valid_enemy(self, enemy):
        return enemy.player_id not in [-1, self.player_id] and enemy.unit_type != TYPE_PROJECTILE

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

    def single_attack(self, game, damage=None):
        if self.delay <= 0:
            self.target[1].take_damage(self.damage if damage is None else damage, game)
            self.delay += self.delay_time
            return True
        return False

    def throw_projectile(self, game, clazz, spread=0):
        if self.delay <= 0:
            self.delay += self.delay_time
            game.place(clazz, int(self.x), int(self.y), self.player_id, int(self.angle + randint(-spread, spread)),
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

    def kill(self):
        if Unit.game is not None:
            Unit.game.players[self.player_id].power -= self.power_cost
        super().kill()


class Archer(Fighter):
    cost = (1.0, 1.0)
    placeable = False
    name = 'Лучник'
    power_cost = 1  # Поменять
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/archer/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Archer.images[player_id]

        super().__init__(x, y, id, player_id, Archer.images[player_id])
        self.delay_time = 60

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.move_to_point(args[0], args[1], 1, 0.5, 3)

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, args[1])
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
    power_cost = 1  # Поменять
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/soldier/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Soldier.images[player_id]

        super().__init__(x, y, id, player_id, Soldier.images[player_id])

    def update(self, *args):
        if not args:
            return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:

            if self.target[0] == TARGET_MOVE:
                self.move_to_point(args[0], args[1], 1.5, 1, 2)
                return

            if self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, args[1])
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

    def is_valid_enemy(self, enemy):
        return super().is_valid_enemy(enemy) and type(enemy) != Dragon


class Worker(Fighter):
    cost = (5.0, 0.0)
    name = 'Рабочий'
    placeable = False
    power_cost = 3  # Поменять
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/working/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Worker.images[player_id]

        super().__init__(x, y, id, player_id, Worker.images[player_id])
        self.money = 0
        self.wood = 0
        self.capacity = 50
        self.state = STATE_ANY_WORK

    def take_damage(self, dmg, game):
        super().take_damage(dmg, game)
        self.state = STATE_FIGHT
        self.find_new_target(game, 2000)

    def update(self, *args):
        if not args:
            return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:

            if self.target[0] == TARGET_MOVE:
                self.move_to_point(args[0], args[1], 1.5, 1)
                return

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, args[1])
                    if self.state == STATE_FIGHT:
                        self.state = STATE_ANY_WORK
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
                                    self.money += MONEY_PER_PUNCH
                                    if self.is_full():
                                        self.find_new_target(args[1], 3000)
                                        return
                            elif type(self.target[1]) == Tree:
                                if self.single_attack(args[1]):
                                    self.wood += WOOD_PER_PUNCH
                                    if self.is_full():
                                        self.find_new_target(args[1], 3000)
                                        return
                            elif type(self.target[1]) == UncompletedBuilding:
                                if self.single_attack(args[1], -5):
                                    if self.target[1].health >= self.target[1].max_health:
                                        if not self.find_new_target(args[1], 3000):
                                            self.set_target(TARGET_NONE, None)
                                            return
                            elif type(self.target[1]) == Fortress and self.player_id == self.target[1].player_id:
                                args[1].give_resources(self.player_id, (self.money, self.wood))
                                self.money = 0
                                self.wood = 0
                                self.find_new_target(args[1], 3000)
                                return
                            else:
                                self.single_attack(args[1])
                    else:
                        self.move_to_angle(1.5, args[1])
                elif not near:
                    self.move_to_angle(1, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1], 3000)

        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return

    def is_full(self):
        return self.money + self.wood * 5 > 50

    def is_valid_enemy(self, enemy):
        if self.is_full():
            return type(enemy) == Fortress and enemy.player_id == self.player_id
        if self.state == STATE_ANY_WORK:
            return type(enemy) in [Mine, Tree, UncompletedBuilding] and enemy.player_id in [-1, self.player_id]
        if self.state == STATE_DIG:
            return type(enemy) == Mine
        elif self.state == STATE_CHOP:
            return type(enemy) == Tree
        elif self.state == STATE_BUILD:
            return type(enemy) == UncompletedBuilding
        elif self.state == STATE_FIGHT:
            return super().is_valid_enemy(enemy) and type(enemy) != Dragon


class ProductingBuild(Unit):
    def __init__(self, x, y, id, player_id, delay, valid_types):
        self.time = delay
        self.delay = delay
        self.units_tray = []
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

    level_costs = [(50.0, 15.0), (20.0, 30.0)]  # Поменять
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/fortress/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

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
        super().__init__(x, y, id, player_id, 2, [Worker])
        self.level = 0
        self.can_upgraded = True
        Fortress.instances.append(self)

    def update(self, *args):
        super().update(*args)
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
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


class Forge(Unit):
    name = 'Кузня'
    placeable = True
    cost = (1.0, 0.0)

    level_costs = [(50.0, 15.0), (20.0, 30.0), (30.0, 40.0)]  # Поменять
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/forge/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    @staticmethod
    def get_mult(unit):
        if Unit.game is None:
            return 1.0, 1.0
        if unit.unit_type in [TYPE_RESOURCE, TYPE_DECOR]:
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
            if type(unit) != UncompletedBuilding:
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

    def update(self, *args):
        super().update(*args)
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return

    def next_level(self, game):
        if self.level == 4:
            print('Already on max level!')
            return
        self.level += 1
        if game.players[self.player_id].max_forge_level < self.level:
            game.players[self.player_id].max_forge_level = self.level

        for obj in game.all_sprites:
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


class Casern(ProductingBuild):
    placeable = True
    name = 'Казарма'
    cost = (1.0, 0.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/casern/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = Casern.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Archer, Soldier])


class DragonLore(ProductingBuild):
    placeable = True
    name = 'Драконье логово'
    cost = (1.0, 0.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/dragonlair/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = DragonLore.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Dragon])


class Workshop(ProductingBuild):
    placeable = True
    name = 'Мастерская'
    cost = (1.0, 0.0)
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/workshop/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.image = Workshop.images[player_id]
        super().__init__(x, y, id, player_id, 5, [Ballista])


class ArcherTower(Fighter):
    cost = (1.0, 1.0)
    placeable = True
    name = 'Башня'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/turret/{team_id[i]}.png'))
    image = images[0]
    required_level = 2  # Поменять этот пример
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id):
        self.archer_image = Archer.images[player_id]
        self.tower_image = ArcherTower.images[player_id]

        super().__init__(x, y, id, player_id, ArcherTower.images[player_id])
        self.update_image()

    def update_image(self):
        self.image = Surface(self.tower_image.get_rect().size, pygame.SRCALPHA)
        self.image.blit(self.tower_image, (0, 0))
        self.image.blit(pygame.transform.rotate(self.archer_image, -self.angle), (10, 10))

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.find_target_angle()
                turned = self.turn_around(3)

                if args[0].type == SERVER_EVENT_UPDATE:
                    if turned:
                        self.set_target(TARGET_NONE, None, args[1])
                        return

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None)
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                if self.turn_around(3):
                    if args[0].type == SERVER_EVENT_UPDATE:
                        self.throw_projectile(args[1], Arrow)

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])


class Tree(Unit):
    placeable = False
    name = 'Дерево'
    tree = pygame.image.load('sprite-games/building/tree/tree.png')
    image = tree
    required_level = 1
    unit_type = TYPE_RESOURCE

    def __init__(self, x, y, id, player_id):
        self.image = Tree.tree
        super().__init__(x, y, id, player_id)
        self.max_health = 10
        self.health = self.max_health

    def update(self, *args):
        if args[0].type == SERVER_EVENT_UPDATE:
            if not self.is_alive():
                args[1].kill(self)


class FireProjectile(TwistUnit):
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

    def update(self, *args):
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            self.time += 1
            if self.time >= 15:
                self.time = 0
                self.current_state += 1
                if args[0].type == CLIENT_EVENT_UPDATE:
                    self.current_state = min(5, self.current_state)
                    self.update_image()
                elif args[0].type == SERVER_EVENT_UPDATE:
                    if self.current_state == 6:
                        args[1].kill(self)
                        print('Dead')
                        return
                    for spr in args[1].get_intersect(self):
                        if (spr != self) and (spr.unit_type != TYPE_PROJECTILE) \
                                and (spr.player_id not in [self.player_id, -1]) and type(spr) != Dragon:
                            spr.take_damage(self.damage, args[1])

    def get_args(self):
        print(self.angle)
        return f'_{self.angle}'

    def update_image(self):
        rotated_image = pygame.transform.rotate(FireProjectile.images[self.current_state], -self.angle)
        self.image = rotated_image


class Dragon(Fighter):
    cost = (5.0, 0.0)
    power_cost = 5  # Поменять
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
    required_level = 1  # Will be removed
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.time = 0
        self.anim_switch = 0
        self.anim_tuple = Dragon.images[player_id]

        super().__init__(x, y, id, player_id, Soldier.images[player_id])
        self.update_image()
        self.delay = 45 * 10

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type == CLIENT_EVENT_UPDATE:
            self.time += 1
            if self.time >= 45:
                self.anim_switch = (self.anim_switch + 1) % 2
                self.time = 0
                self.update_image()

        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:

            if self.target[0] == TARGET_MOVE:
                self.move_to_point(args[0], args[1], 1, 0.5)
                return

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, args[1])
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack()
                if self.turn_around(2):
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            self.throw_projectile(args[1], FireProjectile)
                    else:
                        self.move_to_angle(1, args[1])
                elif not near:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])

    def update_image(self):
        rotated_image = pygame.transform.rotate(self.anim_tuple[self.anim_switch], -self.angle)
        self.image = rotated_image


class UncompletedBuilding(Unit):
    placeable = False
    unit_type = TYPE_BUILDING

    def __init__(self, x, y, id, player_id, clazz_id):
        self.clazz = UNIT_TYPES[int(clazz_id)]
        self.image = UNIT_TYPES[int(clazz_id)].image
        super().__init__(x, y, id, player_id)
        self.health = 1
        self.max_health = 100
        self.completed = False

    def update(self, *args):
        if args is None:
            return
        if args[0].type == SERVER_EVENT_UPDATE:
            if not self.is_alive():
                args[1].kill(self)
                return
            if self.health >= self.max_health:
                args[1].place(self.clazz, int(self.x), int(self.y), self.player_id,
                              ignore_space=True, ignore_money=True, ignore_fort_level=True)
                self.completed = True
                print('Ready')

    def get_args(self):
        return f'_{get_class_id(self.clazz)}'

    def take_damage(self, dmg, game):
        if not self.completed:
            super().take_damage(dmg, game)

    def is_alive(self):
        return super().is_alive() and not self.completed


class Ballista(Fighter):
    cost = (1.0, 1.0)
    placeable = False
    power_cost = 3  # Поменять
    name = 'Баллиста'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/ballista/{team_id[i]}.png'))
    image = images[0]
    required_level = 1  # Will be removed
    unit_type = TYPE_FIGHTER

    def __init__(self, x, y, id, player_id):
        self.image = Ballista.images[player_id]
        super().__init__(x, y, id, player_id, Ballista.images[player_id])
        self.delay_time = 180

    def update(self, *args):
        if not args:
            return
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
            if self.target[0] == TARGET_MOVE:
                self.move_to_point(args[0], args[1], 1, 0.5, 1)
                # у лучника эти аргументы больше,думаю логично что баллиста более неповоротливая

            elif self.target[0] == TARGET_ATTACK:
                if args[0].type == SERVER_EVENT_UPDATE and not self.target[1].is_alive():
                    self.set_target(TARGET_NONE, None, args[1])
                    return

                self.find_target_angle()
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.update_delay()
                near = self.close_to_attack(1500)
                if self.turn_around(3):
                    if near:
                        if args[0].type == SERVER_EVENT_UPDATE:
                            self.throw_projectile(args[1], BallistaArrow)
                    else:
                        self.move_to_angle(1, args[1])
                elif not near:
                    self.move_to_angle(0.5, args[1])

            elif self.target[0] == TARGET_NONE:
                if args[0].type == SERVER_EVENT_UPDATE:
                    self.find_new_target(args[1])


class Farm(Unit):
    name = 'Ферма'
    placeable = True
    cost = (1.0, 0.0)

    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/building/farm/{team_id[i]}.png'))
    image = images[0]
    required_level = 1
    unit_type = TYPE_BUILDING

    instances = []

    @staticmethod
    def get_player_meat(player_id):
        meat = 0
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

    def update(self, *args):
        super().update(*args)
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return


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
    17: Farm
}

UNIT_STATS = {  # (max_health, base_dmg)
    Soldier: (50, 10),  # Soldier,
    Mine: (1000, 0),  # Mine,
    Archer: (50, 0),  # Archer,
    Arrow: (1, 5),  # Arrow,
    Casern: (150, 0),  # Casern,
    Fortress: (250, 0),  # Fortress,
    Worker: (75, 1),  # Worker,
    ArcherTower: (75, 0),  # ArcherTower,
    Tree: (100, 0),  # Tree,
    Dragon: (100, 0),  # Dragon,
    FireProjectile: (1, 1),  # FireProjectile,
    UncompletedBuilding: (100, 0),  # UncompletedBuilding,
    Ballista: (100, 0),  # Ballista,
    BallistaArrow: (1, 25),  # BallistaArrow,
    DragonLore: (150, 0),  # DragonLore,
    Workshop: (150, 0),  # Workshop,
    Forge: (150, 0),  # Forge
    Farm: (150, 0)  # Farm
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
