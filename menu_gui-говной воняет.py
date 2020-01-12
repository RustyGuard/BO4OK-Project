from pygame.surface import Surface
from pygame_gui.core.drawable_shapes import DrawableShape, RoundedRectangleShape, RectDrawableShape, \
    EllipseDrawableShape

from headpiece import Headpiece
from play import Play
import pygame
from pygame_gui import UIManager
from pygame_gui.elements import UIButton, UILabel

# pygame.mixer.init()
# pygame.mixer.music.load('3.mp3')
# pygame.mixer.music.play(-1)
from pygame_gui_tools import NoFrameButton

background = pygame.image.load('sprite-games/menu/background.png')
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# Headpiece.play(screen)
screen.blit(background, (0, 0))
FPS = 60


# image = {"play": (28, 950),
#          "settings": (400, 950),
#          "statistics": (772, 950),
#          "creators": (1145, 950),
#          "exit": (1590, 950)}
#
#
# class Button(pygame.sprite.Sprite):
#     def __init__(self, group, name):
#         super().__init__(group)
#         self.stok_image = pygame.image.load(f'sprite-games/menu/{name}.png')
#         self.anim = pygame.image.load(f'sprite-games/menu/anim/{name}.png')
#         self.name = name
#         self.image = self.stok_image
#         self.rect = self.image.get_rect()
#         self.rect.topleft = image[name]
#
#     def get_anim(self, event):
#         if self.rect.collidepoint(event.pos):
#             self.image = self.anim
#         else:
#             if self.image == self.anim:
#                 self.image = self.stok_image
#
#     def get_event(self, event):
#         if self.rect.collidepoint(event.pos):
#             if self.name == "play":
#                 Play().play(screen)
#             if self.name == "settings":
#                 Headpiece.play(screen)
#             if self.name == "statistics":
#                 Headpiece.play(screen)
#             if self.name == "creators":
#                 Headpiece.play(screen)
#             if self.name == "exit":
#                 exit()


class Cursor(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.image = pygame.image.load('sprite-games/menu/cursor.png')
        self.rect = self.image.get_rect()


# all_buttons = pygame.sprite.Group()
# for i in image:
#     Button(all_buttons, i)
manager = UIManager(screen.get_size(), 'sprite-games/menu/menu.json')
ready_button = NoFrameButton(
    pygame.Rect(28, 950, 359, 90),
    '', manager, object_id='ready')

running = True
clock = pygame.time.Clock()
all_cursor = pygame.sprite.Group()
cursor = Cursor(all_cursor)
pygame.mouse.set_visible(0)
f = False
while running:
    for event in pygame.event.get():
        manager.process_events(event)
        if event.type == pygame.QUIT:
            exit()
        elif event.type == pygame.USEREVENT:
            if event.ui_element == ready_button:
                print('Disabled')
                ready_button.disable()
        # if event.type == pygame.MOUSEMOTION:
        #     for button in all_buttons:
        #         button.get_anim(event)
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     for button in all_buttons:
        #         button.get_event(event)
    manager.update(1 / 60)
    screen.blit(background, (0, 0))
    manager.draw_ui(screen)
    # all_buttons.draw(screen)
    cursor.rect.topleft = pygame.mouse.get_pos()
    all_cursor.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
