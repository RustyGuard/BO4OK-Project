import pygame
from data import headpiece, Music, play, settings, statistics, titers, ip, gameover, menu
from server import main
from client import ClientWait

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
music = Music("menu", ["creators", "build_a_farm", "click",
                       "construction_completed", "eror",
                       "investigation_completed", "headpiece"])

window = "headpiece"  # запуск игрового цикла
ip_host = nicname = None
while window:  # P.s Это сдаелано для оптимизации,дабы инициализации других окон не весела в программе
    music.update(window)
    if window == "headpiece":
        window = headpiece(screen)
        pygame.mixer.music.play(-1)
    elif window == "play":
        window, nicname = play(screen)
    elif window == "settings":
        window = settings(screen)
    elif window == "statistics":
        window = statistics(screen)
    elif window == "creators":
        window = titers(screen)
    elif window == "host":
        main(screen)
        window = "play"
    elif window == "connect":
        window, ip_host = ip(screen)
    elif window == "OK":
        game = ClientWait().play(screen, ip_host if ip_host != '' else 'localhost', nick=nicname)
        if game:
            music.update("headpiece")
            gameover(screen, game)
        window = "connect"
    elif window == "menu":
        window = menu(screen)
    elif window == "exit":
        break
pygame.quit()
