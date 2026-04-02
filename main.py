"""
Abyssal Descent — A Roguelike Dungeon Crawler
=============================================
Author  : (your name here)
Engine  : Python 3 + Pygame
License : MIT
"""

import pygame
import sys
from game import Game

def main():
    pygame.init()
    pygame.display.set_caption("Abyssal Descent")
    screen = pygame.display.set_mode((1100, 700), pygame.RESIZABLE)
    clock  = pygame.time.Clock()

    game = Game(screen)
    game.new_game()

    while True:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                game.screen = screen
            game.handle_event(event)
        game.render()
        pygame.display.flip()

if __name__ == "__main__":
    main()
