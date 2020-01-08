from headpiece import headpiece
import pygame

# Вызов заставки
# headpiece.play()
# Вызов заставки
background = pygame.image.load('sprite-games/menu/background.png')
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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


class Cursor(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.image = pygame.image.load('sprite-games/menu/cursor.png')
        self.rect = self.image.get_rect()


all_buttons = pygame.sprite.Group()
for i in ["creators", "exit", "play", "settings", "statistics"]:
    Button(all_buttons, i)
running = True
clock = pygame.time.Clock()
all_cursor = pygame.sprite.Group()
cursor = Cursor(all_cursor)
Timer = 0
pygame.mouse.set_visible(0)
f = False
while running:
    screen.fill(pygame.Color("white"))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            for button in all_buttons:
                button.get_anim(event)
    screen.blit(background, (0, 0))
    all_buttons.draw(screen)
    cursor.rect.topleft = pygame.mouse.get_pos()
    all_cursor.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()