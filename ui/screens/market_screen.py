import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import STALL, STALL_EDGE, TEXT, MUTED

class MarketScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.time_left = None
        self.font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)

    def set_time_left(self, t):
        self.time_left = t

    def render(self, surface):
        # play area
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, (24,24,30), (0, 0, play_w, self.cfg.window_h))

        # stalls
        for st in self.episode.market.stalls:
            x,y,w,h = st.rect
            pygame.draw.rect(surface, STALL, st.rect, border_radius=8)
            pygame.draw.rect(surface, STALL_EDGE, st.rect, width=2, border_radius=8)
            draw_text(surface, st.name, x+8, y+8, self.small, TEXT)
            draw_text(surface, f"Items: {len(st.items)}", x+8, y+26, self.small, MUTED)

        # teams
        for team in self.episode.teams:
            pygame.draw.circle(surface, team.color, (int(team.x), int(team.y)), 10)
            draw_text(surface, team.name, int(team.x)+12, int(team.y)-10, self.small, team.color)

        render_hud(surface, self.cfg, self.episode, "MARKET", time_left=self.time_left)
