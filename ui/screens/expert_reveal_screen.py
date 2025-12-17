import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text, draw_panel
from constants import BG, TEXT, MUTED, GOOD, BAD, GOLD


class ExpertRevealScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 28)
        self.small = pygame.font.SysFont(None, 18)
        self.micro = pygame.font.SysFont(None, 16)
        self.choice_include = True
        self.cursor = 0
        self.is_done = False
        self.auto_timer = 0.0
        self.auto_delay = 3.2

    def reset(self):
        self.choice_include = True
        self.cursor = 0
        self.is_done = False
        self.auto_timer = 0.0
        self._sync_cursor()

    def _pending_teams(self):
        return [t for t in self.episode.teams if t.expert_pick_item and t.expert_pick_included is None]

    def _sync_cursor(self):
        pending = self._pending_teams()
        if not pending:
            self.is_done = True
            return
        self.is_done = False
        self.cursor = min(self.cursor, len(pending) - 1)
        team = pending[self.cursor]
        self.choice_include = self._default_choice(team)
        self.auto_timer = 0.0

    def _default_choice(self, team):
        pick = team.expert_pick_item
        if not pick:
            return False
        estimate = pick.appraised_value or pick.attributes.get("expert_estimate", pick.shop_price)
        return (estimate - pick.shop_price) >= 2.0

    def decisions_complete(self) -> bool:
        return self.is_done

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.is_done:
            return
        pending = self._pending_teams()
        if not pending:
            return

        if event.key in (pygame.K_LEFT, pygame.K_DOWN):
            self.choice_include = False
            self.auto_timer = 0.0
        elif event.key in (pygame.K_RIGHT, pygame.K_UP):
            self.choice_include = True
            self.auto_timer = 0.0
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._apply_choice(pending[self.cursor])

    def _apply_choice(self, team):
        self.episode.mark_expert_choice(team, self.choice_include)
        self.cursor += 1
        self._sync_cursor()

    def update(self, dt: float):
        if self.is_done:
            return
        self.auto_timer += dt
        pending = self._pending_teams()
        if pending and self.auto_timer >= self.auto_delay:
            self._apply_choice(pending[self.cursor])

    def _render_choice_buttons(self, surface, x, y):
        include_color = GOOD if self.choice_include else MUTED
        exclude_color = BAD if not self.choice_include else MUTED
        draw_text(surface, "Include in results  [→]", x, y, self.small, include_color); y += 20
        draw_text(surface, "Leave it out       [←]", x, y, self.small, exclude_color)

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Expert Reveal", 24, 18, self.font, TEXT)
        draw_text(surface, "Decide whether to auction the expert item after the team lots.", 24, 46, self.small, MUTED)

        pending = self._pending_teams()
        if not pending:
            draw_text(surface, "All expert picks resolved. Moving to results.", 24, 82, self.small, GOOD)
        else:
            team = pending[self.cursor]
            pick = team.expert_pick_item
            draw_text(surface, f"Team: {team.name}  (Expert: {team.expert.name})", 24, 78, self.small, team.color)

            panel_rect = (20, 110, play_w - 40, 200)
            draw_panel(surface, panel_rect)
            draw_text(surface, f"Expert reveals: {pick.name}", 32, 126, self.font, GOLD)
            draw_text(surface, f"Paid: ${pick.shop_price:0.0f}", 32, 158, self.small, TEXT)
            est = pick.appraised_value or pick.attributes.get("expert_estimate", pick.shop_price)
            draw_text(surface, f"Estimated resale: ${est:0.0f}", 32, 182, self.small, GOOD if est >= pick.shop_price else BAD)
            draw_text(surface, pick.attributes.get("description", "Choice is yours — include it or not."), 32, 206, self.micro, MUTED)

            self._render_choice_buttons(surface, 32, 236)
            draw_text(surface, "Press ENTER to confirm • Auto-decides if you wait", 32, 270, self.micro, MUTED)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "EXPERT_REVEAL",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
