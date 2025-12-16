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

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, (16,22,18), (0, 0, play_w, self.cfg.window_h))

        draw_text(surface, "Results", 24, 18, self.font, TEXT)
        y = 64

        draw_text(surface, f"Winner: {self.episode.winner.name} (Profit {self.episode.winner.profit:+.0f})", 24, y, self.small, TEXT)
        y += 24

        for team in self.episode.teams:
            draw_text(surface, team.name, 24, y, self.small, team.color)
            if team.golden_gavel:
                draw_text(surface, "GOLDEN GAVEL", 130, y, self.small, GOLD)
            y += 18

            draw_text(surface, f"Spent ${team.spend:.0f} | Revenue ${team.revenue:.0f} | Profit {team.profit:+.0f}", 36, y, self.small, MUTED)
            y += 18

            for it in team.items_bought:
                tag = " [EXPERT]" if it.is_expert_pick else ""
                profit = it.auction_price - it.shop_price
                col = GOOD if profit > 0 else BAD
                draw_text(surface, f"{it.name}{tag}", 36, y, self.small, TEXT); y += 16
                draw_text(surface, f"Paid ${it.shop_price:.0f} -> Sold ${it.auction_price:.0f} (Δ {profit:+.0f})", 56, y, self.small, col); y += 18
            y += 10

        draw_text(surface, "SPACE: skip phases | Close window to exit", 24, self.cfg.window_h - 26, self.small, MUTED)
        render_hud(surface, self.cfg, self.episode, "RESULTS", time_left=None)
