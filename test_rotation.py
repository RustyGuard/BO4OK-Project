import pygame
import math

size = width, height = 500, 500
fps = 120
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
running = True
units = pygame.sprite.Group()
move = 30
pygame.time.set_timer(move, 15)


class Unit(pygame.sprite.Sprite):
    image = pygame.image.load('sprites/test_unit.png')

    def __init__(self, x, y):
        super().__init__(units)
        self.x = x
        self.y = y
        self.orig_image = Unit.image
        self.rect = pygame.Rect(x, y, 20, 20)
        self.add(units)

    def update(self, *args):
        angle = (180 / math.pi) * -math.atan2(args[1] - self.y, args[0] - self.x)
        self.image = pygame.transform.rotate(self.orig_image, int(angle))
        # self.rect = self.image.get_rect(center=self.position)


while running:
    screen.fill(pygame.Color('white'))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                Unit(*event.pos)
    units.update(*pygame.mouse.get_pos())
    units.draw(screen)
    pygame.display.flip()
    clock.tick(fps)
pygame.quit()
