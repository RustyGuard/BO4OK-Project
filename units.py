import math

import pygame
from pygame.sprite import Sprite
from constants import SERVER_EVENT_SEC, SERVER_EVENT_UPDATE, CLIENT_EVENT_SEC, CLIENT_EVENT_UPDATE

# States
STATE_IDLE = 0
STATE_TURN_AROUND = 1
STATE_MOVE = 2
STATE_ATTACK = 3

TARGET_MOVE = 0
TARGET_ATTACK = 1


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
        super().__init__()

    def move(self, x, y):
        if x != 0 or y != 0:
            self.x += x
            self.y += y
            self.update_rect()

    def set_offset(self, x, y):
        self.offsetx, self.offsety = x, y
        self.update_rect()

    def update_rect(self):
        self.rect.centerx = int(self.x) + self.offsetx
        self.rect.centery = int(self.y) + self.offsety

    def get_args(self):
        return ''


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
        center = self.default_image.get_rect().center
        rotated_image = pygame.transform.rotate(Soldier.image, -self.angle)
        new_rect = rotated_image.get_rect(center=center)
        new_rect.centerx = self.rect.centerx
        new_rect.centery = self.rect.centery
        self.image = rotated_image
        self.rect = new_rect

    def move_to_angle(self, speed):
        self.move(math.cos(math.radians(self.angle)) * speed, math.sin(math.radians(self.angle)) * speed)


class Mine(Unit):
    cost = 100.0
    mine = pygame.image.load('sprite-games/building/mine/mine.png')

    def __init__(self, x, y, id, player_id):
        self.image = Mine.mine
        super().__init__(x, y, id, player_id)

    def update(self, *args):
        if not self.live:
            return
        if args:
            if args[0].type == SERVER_EVENT_SEC:
                args[1].players[self.player_id].money += 5


class Fighter(TwistUnit):
    def __init__(self, x, y, id, player_id, default_image):
        super().__init__(x, y, id, player_id, default_image)
        self.target_angle = 0
        self.target = None
        self.has_target = True

    def set_target(self, target_type, coord):
        self.target = (target_type, coord)

    def find_target_angle(self):
        self.target_angle = int(
            math.degrees(math.atan2(self.target[1][1] - self.rect.centery, self.target[1][0] - self.rect.centerx)))
        if self.target_angle < 0:
            self.target_angle += 360


class Soldier(Fighter):
    cost = 10.0
    image = pygame.image.load('sprite-games/warrior/soldier/soldier.png')

    def __init__(self, x, y, id, player_id):
        self.image = Soldier.image

        super().__init__(x, y, id, player_id, Soldier.image)

    def update(self, *args):
        if not self.live:
            return
        if args:
            if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
                if self.target is not None:

                    xr = self.target[1][0] - self.rect.centerx
                    yr = self.target[1][1] - self.rect.centery
                    if math.sqrt(xr * xr + yr * yr) < 40:
                        self.target = None
                        return
                    self.find_target_angle()
                    angle_diff = self.target_angle - self.angle

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
                    else:
                        self.move_to_angle(1)
                    # self.set_angle(self.target_angle)
                    # self.move_to_angle(1)
                else:
                    pass
                    # self.add_angle(1)


UNIT_TYPES = {
    0: Soldier,
    1: Mine
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
