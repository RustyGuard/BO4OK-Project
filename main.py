import pygame
import data
import server

pygame.init()
pygame.mixer.init()
pygame.mouse.set_visible(False)

musik = pygame.mixer.music.load('music/menu.mp3')
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
data.headpiece(screen)
window, nicname = data.menu(screen)
while window:
    if window == "play":
        window, nicname = data.play(screen)
    if window == "settings":
        window = data.settings(screen)[0]
    if window == "statistics":
        window = "back_menu"
    if window == "creators":
        pygame.mixer.music.pause()
        data.titers(screen)
        window = "back_menu"
        pygame.mixer.music.unpause()
    if window == "host":
        server.main(screen, nicname)
        window = "play"
    if window == "connect":
        window = data.ip(screen)[0]
    if window == "back_menu":
        window = data.menu(screen)[0]
    if window == "exit":
        break
pygame.quit()
