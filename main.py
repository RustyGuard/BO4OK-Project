import pygame
import data
import server

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)


musik = pygame.mixer.Sound('music/menu.ogg')
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
data.headpiece(screen)  # вызов заставки
musik.play(-1)  # запуск фоновой мелодии меню
musik.set_volume(0.2)
window, nicname = data.menu(screen)  # запуск игрового цикла
while window:  # P.s Это сдаелано для оптимизации,дабы инициализации других окон не весела в программе
    if window == "play":
        window, nicname = data.play(screen)
    if window == "settings":
        window = data.settings(screen)[0]
    if window == "statistics":
        window = data.statistics(screen)[0]
    if window == "creators":
        musik.pause()
        data.titers(screen)
        musik.unpause()
        window = "back_menu"
    if window == "host":
        server.main(screen, nicname)
        window = "play"
    if window == "connect":
        window = data.ip(screen, musik)[0]
    if window == "back_menu":
        window = data.menu(screen)[0]
    if window == "exit":
        break
pygame.quit()
