import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from ui.render.stall_card import StallCardRenderer
from constants import BG, GOOD

class MarketScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.time_left = None
        self.font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)
        self.stall_renderer = StallCardRenderer()

    def set_time_left(self, t):
        self.time_left = t

    def render(self, surface):
        # play area
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))

        active_stalls = set()
        for team in self.episode.teams:
            if team.target_stall_id is not None:
                active_stalls.add(team.target_stall_id)
            ctx = team.decision_context or {}
            if ctx.get("stall_id") is not None:
                active_stalls.add(ctx.get("stall_id"))

        for st in self.episode.market.stalls:
            self.stall_renderer.draw(
                surface,
                st,
                self.small,
                self.small,
                is_active=st.stall_id in active_stalls,
            )

        # teams
        for team in self.episode.teams:
            pygame.draw.circle(surface, team.color, (int(team.x), int(team.y)), 10)
            draw_text(surface, team.duo_label(), int(team.x)+12, int(team.y)-10, self.small, team.color)
            if len(team.team_items) >= self.cfg.items_per_team:
                draw_text(surface, "Done shopping", int(team.x)+12, int(team.y)+8, self.small, GOOD)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "MARKET",
            time_left=self.time_left,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
