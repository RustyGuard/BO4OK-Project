import pygame
import pygame_gui

import client
import server


def main_screen():
    pygame.init()
    size = 800, 450
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    manager = pygame_gui.UIManager(size, 'theme.json')
    client_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((size[0] - 150 - 5, size[1] // 2), (150, 50)),
        text='Запустить клиент',
        manager=manager)
    server_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((size[0] - 150 - 5, size[1] // 2 + 55), (150, 50)),
        text='Запустить сервер',
        manager=manager)
    res = None
    while res is None:
        for event in pygame.event.get():
            manager.process_events(event)
            print(event)
            if event.type == pygame.QUIT:
                res = -1
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == client_button:
                        print('0')
                        #res = 0
                    elif event.ui_element == server_button:
                        print('1')
                        #res = 1
        manager.update(1.0 / 60.0)
        screen.fill((0, 125, 255))
        manager.draw_ui(screen)
        pygame.display.flip()
        clock.tick(60)
    if res == 0:
        client.main()
    if res == 1:
        server.main()


if __name__ == '__main__':
    main_screen()
