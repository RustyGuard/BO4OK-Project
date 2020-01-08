from headpiece import Headpiece
import pygame


class Play():
    def __init__(self):
        return

    def play(self, screen):
        background = pygame.image.load('sprite-games/play/Основа.png')
        pygame.init()
        screen.blit(background, (0, 0))
        FPS = 60
        image = {"host": (330, 183),
                 "connect": (330, 386),
                 "back": (330, 784)}

        class Button(pygame.sprite.Sprite):
            def __init__(self, group, name):
                super().__init__(group)
                # self.anim = pygame.image.load(f'sprite-games/menu/anim/{name}.png')
                self.name = name
                self.image = pygame.image.load(f'sprite-games/play/{name}.png')
                self.rect = self.image.get_rect()
                self.rect.topleft = image[name]

            def get_anim(self, event):
                return

            def get_event(self, event):
                if self.rect.collidepoint(event.pos):
                    if self.name == "host":
                        Headpiece.play(screen)
                    if self.name == "connect":
                        Headpiece.play(screen)
                    if self.name == "back":
                        return True

        class Cursor(pygame.sprite.Sprite):
            def __init__(self, group):
                super().__init__(group)
                self.image = pygame.image.load('sprite-games/menu/cursor.png')
                self.rect = self.image.get_rect()

        all_buttons = pygame.sprite.Group()
        for i in image:
            Button(all_buttons, i)
        running = True
        clock = pygame.time.Clock()
        all_cursor = pygame.sprite.Group()
        cursor = Cursor(all_cursor)
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
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for button in all_buttons:
                        a = button.get_event(event)
                        if a:
                            return
            screen.blit(background, (0, 0))
            all_buttons.draw(screen)
            cursor.rect.topleft = pygame.mouse.get_pos()
            all_cursor.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
