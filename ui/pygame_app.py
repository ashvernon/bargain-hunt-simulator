import pygame
from config import GameConfig
from constants import BG
from game_state import GameState

def run_app(seed: int = 123, episode_idx: int = 1):
    cfg = GameConfig()
    pygame.init()
    screen = pygame.display.set_mode((cfg.window_w, cfg.window_h))
    pygame.display.set_caption("Bargain Hunt Simulator (Starter)")
    clock = pygame.time.Clock()

    state = GameState(cfg=cfg, seed=seed, episode_idx=episode_idx)

    running = True
    while running:
        dt = clock.tick(cfg.fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            state.handle_event(event)

        state.update(dt)
        screen.fill(BG)
        state.render(screen)
        pygame.display.flip()

    pygame.quit()
