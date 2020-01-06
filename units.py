import math

import pygame
from pygame.sprite import Sprite
from constants import SERVER_EVENT_SEC, SERVER_EVENT_UPDATE, CLIENT_EVENT_SEC, CLIENT_EVENT_UPDATE


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


class Mine(Unit):
    cost = 100.0
    mine = pygame.image.load('sprite-games/building/mine/mine.png')

    def __init__(self, x, y, id, player_id):
        self.image = Mine.mine
        super().__init__(x, y, id, player_id)

    def update(self, *args):
        if args:
            if args[0].type == SERVER_EVENT_SEC:
                args[1].players[self.player_id].money += 5


class Soldier(Unit):
    cost = 10.0
    image = pygame.image.load('sprite-games/warrior/soldier/soldier.png')

    def __init__(self, x, y, id, player_id):
        self.angle = 0
        self.image = Soldier.image
        self.target_angle = 0
        self.target = None

        super().__init__(x, y, id, player_id)
        self.has_target = True

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
        center = Soldier.image.get_rect().center
        rotated_image = pygame.transform.rotate(Soldier.image, -self.angle)
        new_rect = rotated_image.get_rect(center=center)
        new_rect.centerx = self.rect.centerx
        new_rect.centery = self.rect.centery
        self.image = rotated_image
        self.rect = new_rect

    def update(self, *args):
        if args:
            if args[0].type in [SERVER_EVENT_UPDATE, CLIENT_EVENT_UPDATE]:
                if self.target is not None:
                    xr = self.target[0] - self.rect.centerx
                    yr = self.target[1] - self.rect.centery
                    if math.sqrt(xr * xr + yr * yr) < 50:
                        self.target = None
                        return
                    self.set_angle(int(math.degrees(math.atan2(yr, xr))))
                    self.move(math.cos(math.radians(self.angle)) * 0.5, math.sin(math.radians(self.angle)) * 0.5)


UNIT_TYPES = {
    0: Soldier,
    1: Mine
}


def get_class_id(clazz):
    for i, j in UNIT_TYPES.items():
        if j == clazz:
            return i
