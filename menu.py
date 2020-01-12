from headpiece import Headpiece
from play import Play
import pygame
# pygame.mixer.init()
# pygame.mixer.music.load('3.mp3')
# pygame.mixer.music.play(-1)
background = pygame.image.load('sprite-games/menu/background.png')
cursor = pygame.image.load('sprite-games/menu/cursor.png')
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# Headpiece.play(screen)
screen.blit(background, (0, 0))
FPS = 60
image = {"play": (28, 950),
         "settings": (400, 950),
         "statistics": (772, 950),
         "creators": (1145, 950),
         "exit": (1590, 950)}


class Button(pygame.sprite.Sprite):
    def __init__(self, group, name):
        super().__init__(group)
        self.stok_image = pygame.image.load(f'sprite-games/menu/{name}.png')
        self.anim = pygame.image.load(f'sprite-games/menu/anim/{name}.png')
        self.name = name
        self.image = self.stok_image
        self.rect = self.image.get_rect()
        self.rect.topleft = image[name]

    def get_anim(self, event):
        if self.rect.collidepoint(event.pos):
            self.image = self.anim
        else:
            if self.image == self.anim:
                self.image = self.stok_image


all_buttons = pygame.sprite.Group()
for i in image:
    Button(all_buttons, i)
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.MOUSEMOTION:
            for button in all_buttons:
                button.get_anim(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in all_buttons:
                if button.rect.collidepoint(event.pos):
                    if button.name == "play":
                        Play().play(screen)
                    if button.name == "settings":
                        Headpiece.play(screen)
                    if button.name == "statistics":
                        Headpiece.play(screen)
                    if button.name == "creators":
                        Headpiece.play(screen)
                    if button.name == "exit":
                        exit()
    screen.blit(background, (0, 0))
    all_buttons.draw(screen)
    screen.blit(cursor, (pygame.mouse.get_pos()[0] - 9, pygame.mouse.get_pos()[1] - 5))
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
