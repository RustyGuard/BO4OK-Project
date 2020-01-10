import math

import pygame
from pygame import Color
from pygame.rect import Rect
from pygame.sprite import Sprite
from constants import SERVER_EVENT_SEC, SERVER_EVENT_UPDATE, CLIENT_EVENT_SEC, CLIENT_EVENT_UPDATE

# States
STATE_IDLE = 0
STATE_TURN_AROUND = 1
STATE_MOVE = 2
STATE_ATTACK = 3

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
        self.state = STATE_IDLE
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
    cost = 100.0
    placeable = True
    name = 'Mine'
    mine = pygame.image.load('sprite-games/building/mine/mine.png')
    image = mine

    def __init__(self, x, y, id, player_id):
        self.image = Mine.mine
        super().__init__(x, y, id, player_id)

    def update(self, *args):
        if not self.is_alive():
            if args[0].type == SERVER_EVENT_UPDATE:
                args[1].kill(self)
                return
        if args:
            if args[0].type == SERVER_EVENT_SEC:
                args[1].players[self.player_id].money += 5


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
                    # print('Arrow disappears.')
                for spr in args[1].get_intersect(self):
                    if spr != self and spr.player_id != self.player_id and not spr.is_projectile:
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

    def find_new_target(self, game):
        area = Sprite()
        area.rect = Rect(0, 0, 1500, 1500)
        area.rect.center = self.rect.center
        current = None
        for spr in game.get_intersect(area):
            if spr != self and self.is_valid_enemy(spr):
                if current is None:
                    current = (spr, math.sqrt((spr.x - self.x) ** 2 + (spr.x - self.x) ** 2))
                else:
                    dist = math.sqrt((spr.x - self.x) ** 2 + (spr.x - self.x) ** 2)
                    if dist < current[1]:
                        current = (spr, dist)
        if current:
            self.set_target(TARGET_ATTACK, current[0])
            game.server.send_all(f'2_{TARGET_ATTACK}_{self.id}_{current[0].id}')
            return True
        return False

    def is_valid_enemy(self, enemy):
        return enemy.player_id != self.player_id and not enemy.is_projectile

    def turn_around(self):
        angle_diff = self.target_angle - self.angle
        if angle_diff == 0:
            return True
        if angle_diff < 0:
            if abs(angle_diff) >= 180:
                self.add_angle(1)
            else:
                self.add_angle(-1)
        elif angle_diff > 0:
            if abs(angle_diff) >= 180:
                self.add_angle(-1)
            else:
                self.add_angle(1)
        return False

    def single_attack(self, game):
        if self.delay <= 0:
            self.target[1].take_damage(self.damage, game)
            self.delay += self.delay_time
            # print('Awww', self.target[1].id, self.target[1].health)

    def throw_projectile(self, game, clazz):
        if self.delay <= 0:
            self.delay += self.delay_time
            game.create_entity(clazz, int(self.x), int(self.y), self.player_id, int(self.angle))

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
    cost = 15.0
    placeable = True
    name = 'Archer'
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/archer/{team_id[i]}.png'))
    image = images[0]

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
                if self.turn_around():
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
                if self.turn_around():
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
    cost = 10.0
    name = 'Soldier'
    placeable = True
    images = []
    for i in range(10):
        images.append(pygame.image.load(f'sprite-games/warrior/soldier/{team_id[i]}.png'))
    image = images[0]

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
                if self.turn_around():
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
                if self.turn_around():
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


UNIT_TYPES = {
    0: Soldier,
    1: Mine,
    2: Archer,
    3: Arrow
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
