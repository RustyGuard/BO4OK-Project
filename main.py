import pygame
import data
import server

pygame.init()
pygame.mouse.set_visible(False)

# pygame.mixer.init()
# pygame.mixer.music.load('3.mp3')
# pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
data.headpiece(screen)
window, nicname = data.menu(screen)
while window:
    if window == "play":
        window, nicname = data.play(screen)
    if window == "settings":
        window, nicname = data.settings(screen)
    if window == "statistics":
        window, nicname = ["back_menu", nicname]
    if window == "creators":
        window, nicname = ["back_menu", nicname]
    if window == "host":
        server.main(screen, nicname)
        window, nicname = ["play", nicname]
    if window == "connect":
        window, nicname = data.ip(screen)
    if window == "back_menu":
        window, nicname = data.menu(screen)
    if window == "exit":
        break
pygame.quit()
