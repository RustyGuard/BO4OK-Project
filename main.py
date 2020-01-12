import pygame
import data

pygame.init()
pygame.mouse.set_visible(False)
cursor = pygame.image.load('sprite-games/menu/cursor.png')

pygame.mixer.init()
pygame.mixer.music.load('3.mp3')
pygame.mixer.music.play(-1)

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
data.headpiece(screen)
data.menu(screen)
pygame.quit()
