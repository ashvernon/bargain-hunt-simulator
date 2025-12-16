import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import TEXT, MUTED, GOOD, BAD


class ExpertDecisionScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 18)
        self.cursor = 0
        self.decision_timer = 0.0
        self._sync_cursor()

    def _sync_cursor(self):
        events = getattr(self.episode, "expert_purchase_events", [])
        while self.cursor < len(events) and events[self.cursor]["decision"] is not None:
            self.cursor += 1

    def handle_event(self, event):
        if not getattr(self.episode, "expert_purchase_events", None):
            return
        if event.type != pygame.KEYDOWN:
            return

        if self.cursor >= len(self.episode.expert_purchase_events):
            return

        # Manual input no longer controls the outcome; teams choose for themselves.
        # Keep keypresses from pausing progression.
        return

    def update(self, dt: float):
        self._sync_cursor()
        if not getattr(self.episode, "expert_purchase_events", None):
            return

        if self.cursor >= len(self.episode.expert_purchase_events):
            return

        self.decision_timer -= dt
        if self.decision_timer <= 0:
            self.episode.auto_decide_expert_purchase(self.cursor)
            self.cursor += 1
            self._sync_cursor()
            self.decision_timer = 0.9 / getattr(self.episode, "time_scale", 1.0)

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, (18, 20, 28), (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Expert Leftover Purchases", 24, 18, self.font, TEXT)

        if not getattr(self.episode, "expert_purchase_events", None):
            draw_text(surface, "No proposals", 24, 60, self.small, MUTED)
        elif self.cursor >= len(self.episode.expert_purchase_events):
            draw_text(surface, "All decisions made. Continuing...", 24, 60, self.small, GOOD)
        else:
            event = self.episode.expert_purchase_events[self.cursor]
            team = event["team"]
            draw_text(surface, f"Team: {team.name}", 24, 64, self.small, team.color)
            draw_text(surface, f"Budget left: ${event['leftover_before']:.0f}", 24, 90, self.small, MUTED)

            if event["item"]:
                item = event["item"]
                draw_text(surface, f"Expert suggests: {item.name}", 24, 120, self.small, TEXT)
                draw_text(surface, f"Price: ${item.shop_price:.0f}", 24, 144, self.small, MUTED)
                draw_text(surface, "Team is deciding...", 24, 176, self.small, GOOD)
            else:
                draw_text(surface, "Expert has no suggestion.", 24, 120, self.small, BAD)
                draw_text(surface, "Decision will be recorded automatically", 24, 144, self.small, MUTED)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "EXPERT_DECISION",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
