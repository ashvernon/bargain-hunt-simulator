import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import BG, TEXT, GOOD, BAD, GOLD


class ExpertBudgetScreen(Screen):
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
        if self.timer >= 2.5:
            self.is_done = True

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Handing leftover budget to experts", 24, 18, self.font, TEXT)
        draw_text(surface, "Each team must save at least $1 for their expert bonus buy.", 24, 48, self.small, GOLD)

        y = 86
        for team in self.episode.teams:
            budget = getattr(team, "expert_pick_budget", team.budget_left)
            enough = budget >= self.cfg.expert_min_budget
            color = GOOD if enough else BAD
            draw_text(surface, f"{team.name} gives {team.expert.name} ${budget:0.0f}", 24, y, self.small, team.color); y += 20
            note = "Ready for expert pick" if enough else "Must free up at least $1"
            draw_text(surface, note, 40, y, self.small, color); y += 24

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "EXPERT_HANDOFF",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
