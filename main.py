"""MARS: LAST SIGNAL - run with `python main.py` (add --debug for developer keys)."""
import os, sys
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame
from config import SCREEN_W, SCREEN_H, FPS, TITLE
from core.game import Game
from ui import audio

def main():
    pygame.init()
    audio.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    game = Game(screen, debug="--debug" in sys.argv)
    while game.running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for e in pygame.event.get():
            game.handle_event(e)
        game.update(dt)
        game.draw()
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
