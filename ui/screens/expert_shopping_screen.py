import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import BG, TEXT, MUTED, GOLD, BAD


class ExpertShoppingScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 28)
        self.small = pygame.font.SysFont(None, 18)
        self.is_done = False
        self.timer = 0.0

    def reset(self):
        self.is_done = False
        self.timer = 0.0

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= 2.8:
            self.is_done = True

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Experts head back to the stalls...", 24, 18, self.font, TEXT)
        draw_text(surface, "They must buy within the hand-off budget. Reveal comes after team auctions.", 24, 48, self.small, MUTED)

        y = 90
        for team in self.episode.teams:
            pick = getattr(team, "expert_pick_item", None)
            budget = getattr(team, "expert_pick_budget", 0.0)
            if pick:
                hint = pick.category.title()
                msg = f"{team.expert.name} locks in a secret {hint.lower()} within the ${budget:0.0f} budget"
                draw_text(surface, msg, 24, y, self.small, team.color); y += 18
                draw_text(surface, "Kept sealed until after the team lots sell", 40, y, self.small, GOLD); y += 24
            else:
                draw_text(surface, f"{team.expert.name} couldn't find anything within ${budget:0.0f}", 24, y, self.small, BAD); y += 24

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "EXPERT_SHOPPING",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
