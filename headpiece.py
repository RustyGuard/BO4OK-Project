import pygame


class Headpiece():
    def play(self, screen=pygame.display.set_mode((0, 0), pygame.FULLSCREEN)):
        FPS = 200
        Bo4ok = pygame.image.load('sprite-games/headpiece/Bo4ok.png')
        Games = pygame.image.load('sprite-games/headpiece/Games.png')
        Potick1 = pygame.image.load('sprite-games/headpiece/Potick1.png')
        Potick2 = pygame.image.load('sprite-games/headpiece/Potick2.png')
        Stone = pygame.image.load('sprite-games/headpiece/Stone.png')
        Water = pygame.image.load('sprite-games/headpiece/Water.png')
        Bo4ok_rect = [-900, 500]
        Potick1_rect = [-400, 500]
        running = True
        clock = pygame.time.Clock()
        Timer = 0
        pygame.mouse.set_visible(0)
        f = False
        while running:
            screen.fill(pygame.Color("white"))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            if Bo4ok_rect[0] < 232:
                Bo4ok_rect[0] += 10
                Potick1_rect[0] += 10
            else:
                Potick1 = Potick2
                Bo4ok_rect[0] = 410
                Potick1_rect[0] = 910
                if not f:
                    Timer += 1
                    if Timer == 101:
                        f = True
                        Timer = 0
                if Timer == 300:
                    return
                else:
                    Timer += 1
            screen.blit(Stone, (1170, 500))
            screen.blit(Bo4ok, Bo4ok_rect)
            screen.blit(Potick1, Potick1_rect)
            screen.blit(Games, (1350, 500))
            if f:
                screen.blit(Water, (990, 558))
            pygame.display.flip()
            clock.tick(FPS)
