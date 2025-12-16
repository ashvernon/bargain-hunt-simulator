import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import TEXT, MUTED, GOLD, GOOD, BAD

class ResultsScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 30)
        self.small = pygame.font.SysFont(None, 18)
        self.micro = pygame.font.SysFont(None, 16)

    def _shade(self, color, amount):
        return tuple(max(0, min(255, c + amount)) for c in color)

    def _draw_team_card(self, surface, team, x, y, width):
        item_lines = len(team.items_bought)
        card_height = 70 + item_lines * 34
        bg = self._shade(team.color, 110)
        outline = self._shade(team.color, -30)

        card_rect = pygame.Rect(x, y, width, card_height)
        pygame.draw.rect(surface, bg, card_rect, border_radius=10)
        pygame.draw.rect(surface, outline, card_rect, width=2, border_radius=10)

        inner_y = y + 12
        draw_text(surface, team.name, x + 14, inner_y, self.font, outline)
        if team.golden_gavel:
            draw_text(surface, "GOLDEN GAVEL", x + 170, inner_y + 2, self.small, GOLD)
        inner_y += 26

        profit_col = GOOD if team.profit >= 0 else BAD
        draw_text(
            surface,
            f"Spent ${team.spend:.0f} | Revenue ${team.revenue:.0f} | Profit {team.profit:+.0f}",
            x + 14,
            inner_y,
            self.small,
            profit_col,
        )
        inner_y += 26

        for it in team.items_bought:
            tag = " [EXPERT]" if it.is_expert_pick else ""
            profit = it.auction_price - it.shop_price
            col = GOOD if profit > 0 else BAD
            draw_text(surface, f"{it.name}{tag}", x + 20, inner_y, self.small, TEXT)
            inner_y += 16
            draw_text(
                surface,
                f"Paid ${it.shop_price:.0f} → Sold ${it.auction_price:.0f} (Δ {profit:+.0f})",
                x + 36,
                inner_y,
                self.micro,
                col,
            )
            inner_y += 18

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, (16,22,18), (0, 0, play_w, self.cfg.window_h))

        draw_text(surface, "Results", 24, 18, self.font, TEXT)
        y = 58

        winner = self.episode.winner
        banner_rect = pygame.Rect(18, y, play_w - 36, 54)
        pygame.draw.rect(surface, self._shade(winner.color, 90), banner_rect, border_radius=12)
        pygame.draw.rect(surface, self._shade(winner.color, -20), banner_rect, width=2, border_radius=12)
        draw_text(surface, f"Winner: {winner.name}", 32, y + 10, self.font, TEXT)
        draw_text(surface, f"Total Profit {winner.profit:+.0f}", 32, y + 34, self.small, GOOD if winner.profit >= 0 else BAD)
        y += 74

        for team in self.episode.teams:
            self._draw_team_card(surface, team, 18, y, play_w - 36)
            y += 90 + len(team.items_bought) * 34

        draw_text(surface, "SPACE: skip phases | Close window to exit", 24, self.cfg.window_h - 26, self.small, MUTED)
        render_hud(
            surface,
            self.cfg,
            self.episode,
            "RESULTS",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
