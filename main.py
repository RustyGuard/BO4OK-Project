import pygame
import data
import server
from client import ClientWait

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)


screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
music = data.Music()
music.update("headpiece")
window = data.headpiece(screen)  # вызов заставки, запуск игрового цикла
pygame.mixer.music.play(-1)
ip = nicname = None
while window:  # P.s Это сдаелано для оптимизации,дабы инициализации других окон не весела в программе
    music.update(window)
    if window == "play":
        window, nicname = data.play(screen)
    elif window == "settings":
        window = data.settings(screen)
    elif window == "statistics":
        window = data.statistics(screen)
    elif window == "creators":
        window = data.titers(screen)
    elif window == "host":
        server.main(screen)
        window = "play"
    elif window == "connect":
        window, ip = data.ip(screen)
    elif window == "OK":
        game = ClientWait().play(screen, ip if ip != '' else 'localhost', nick=nicname)
        if game:
            music.update("headpiece")
            data.gameover(screen, game)
        window = "connect"
    elif window == "back_menu":
        window = data.menu(screen)
    elif window == "exit":
        break
    music.update(window)
pygame.quit()
