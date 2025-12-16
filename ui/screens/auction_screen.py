import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from constants import TEXT, MUTED, GOOD, BAD

class AuctionScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 18)
        self.timer = 0.0
        self.step_every = 1.2  # seconds per sale

    def update(self, dt: float):
        if self.episode.auction_done:
            return
        self.timer += dt
        if self.timer >= self.step_every:
            self.timer = 0.0
            self.episode.step_auction()

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, (22,18,18), (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, f"Auction ({self.episode.auction_house.mood})", 24, 18, self.font, TEXT)

        y = 70
        if self.episode.last_sold:
            team, it = self.episode.last_sold
            tag = " [EXPERT]" if it.is_expert_pick else ""
            draw_text(surface, f"Sold: {it.name}{tag}", 24, y, self.small, TEXT); y += 22
            profit = it.auction_price - it.shop_price
            col = GOOD if profit > 0 else BAD
            draw_text(surface, f"Paid ${it.shop_price:.0f} -> Sold ${it.auction_price:.0f}  (Δ {profit:+.0f})", 24, y, self.small, col); y += 22

        # progress
        total = len(self.episode.auction_queue)
        cur = self.episode.auction_cursor
        draw_text(surface, f"Progress: {cur}/{total}", 24, play_w and 120 or 120, self.small, MUTED)

        render_hud(surface, self.cfg, self.episode, "AUCTION", time_left=None)
