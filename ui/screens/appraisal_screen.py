import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import BG, TEXT, MUTED

class AppraisalScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 18)

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Appraisal", 24, 18, self.font, TEXT)

        y = 58
        for team in self.episode.teams:
            draw_text(surface, f"{team.name} (Expert: {team.expert.name})", 24, y, self.small, team.color); y += 20
            for it in team.items_bought:
                tag = " [EXPERT]" if it.is_expert_pick else ""
                draw_text(surface, f"{it.name}{tag}", 30, y, self.small, TEXT); y += 16
                draw_text(surface, f"Paid ${it.shop_price:.0f}  |  Appraised ${it.appraised_value:.0f}", 50, y, self.small, MUTED); y += 18
            y += 12

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "APPRAISAL",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
