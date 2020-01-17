import pygame
import data
import server

pygame.init()
pygame.mouse.set_visible(False)

pygame.mixer.init()
pygame.mixer.music.load('3.mp3')
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
data.headpiece(screen)
window = data.menu(screen)
while window:
    window, nicname = window
    if window == "play":
        window = data.play(screen)
    if window == "settings":
        window = data.settings(screen)
    if window == "statistics":
        pass
    if window == "creators":
        pass
    if window == "host":
        window = server.main(screen, nicname)
    if window == "connect":
        window = data.ip(screen)
    if window == "back_menu":
        window = data.menu(screen)
    if window == "exit":
        break
pygame.quit()
