import os
from pathlib import Path
import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text, draw_panel
from constants import BG, TEXT, MUTED, GOOD, BAD, GOLD, ACCENT, INK, CANVAS, PANEL, PANEL_EDGE


class AuctionScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 18)
        self.big = pygame.font.SysFont(None, 34)
        self.huge = pygame.font.SysFont(None, 48)

        self.stage = "idle"
        self.stage_timer = 0.0
        self.display_price = 0.0
        self.current_lot = None
        self.pending_sale_price = 0.0
        self.bid_history = []
        self.bid_steps = []
        self.bid_total_duration = 0.0
        self.current_bid_idx = -1
        self.active_bidder = None
        self.bid_flash = 0.0
        self.hammer_idx = 0
        self.sold_pause = 1.8
        self.image_cache: dict[str, pygame.Surface | None] = {}
        self.assets_root = Path(__file__).resolve().parent.parent.parent

        self.bidder_names = [
            "Gallery rep",
            "Local dealer",
            "Phone bidder",
            "Online proxy",
            "Vintage scout",
            "Museum intern",
        ]
        self.hammer_lines = ["Going once...", "Going twice...", "Final call..."]

    def _shade(self, color, amount):
        return tuple(max(0, min(255, c + amount)) for c in color)

    def _blend(self, base, tint, weight: float):
        return tuple(int(base[i] * (1 - weight) + tint[i] * weight) for i in range(3))

    def _prepare_next_lot(self):
        if self.episode.auction_cursor >= len(self.episode.auction_queue):
            self.current_lot = None
            return

        lot = self.episode.auction_queue[self.episode.auction_cursor]
        sale_price = self.episode.auction_house.sell(lot.item, self.episode.rng)

        start_price = max(5.0, min(lot.item.shop_price * 0.8, sale_price * 0.85))
        if start_price >= sale_price:
            start_price = sale_price * 0.55

        self.bid_steps, total_time = self._build_bid_script(start_price, sale_price)
        self.bid_total_duration = total_time + 0.9
        self.current_bid_idx = -1
        self.display_price = start_price
        self.pending_sale_price = sale_price
        self.stage = "intro"
        self.stage_timer = 0.0
        self.bid_flash = 0.0
        self.active_bidder = None
        self.current_lot = lot
        self.hammer_idx = 0
        self.bid_history.clear()

    def _build_bid_script(self, start_price: float, sale_price: float):
        steps = []
        time_cursor = 0.7
        bids = self.episode.rng.randint(3, 6)
        chosen_bidders = [self.episode.rng.choice(self.bidder_names) for _ in range(bids)]

        for idx in range(bids):
            bidder = chosen_bidders[idx]
            fraction = (idx + 1) / bids
            reach = start_price + (sale_price - start_price) * (0.55 + 0.45 * fraction)
            reach = min(sale_price, reach)
            steps.append({"time": time_cursor, "amount": reach, "bidder": bidder})
            time_cursor += self.episode.rng.uniform(0.85, 1.15)

        if steps:
            steps[-1]["amount"] = sale_price
        return steps, time_cursor

    def _finalize_sale(self):
        if not self.current_lot:
            return
        self.display_price = self.pending_sale_price
        self.stage = "sold"
        self.stage_timer = 0.0
        self.episode.finalize_auction_sale(self.current_lot, self.pending_sale_price)

    def _peek_next_lot(self):
        offset = 1 if self.current_lot else 0
        nxt_idx = self.episode.auction_cursor + offset
        if nxt_idx < len(self.episode.auction_queue):
            return self.episode.auction_queue[nxt_idx]
        return None

    def _resolve_image_path(self, candidate: Path) -> Path | None:
        """Resolve an image path whether the game is launched from the repo root or elsewhere."""
        if candidate.is_absolute():
            return candidate if candidate.exists() else None

        for root in (Path.cwd(), self.assets_root):
            path = root / candidate
            if path.exists():
                return path
        return None

    def _get_item_image(self, item):
        if item.name in self.image_cache:
            return self.image_cache[item.name]

        # Prefer explicit image path if present on the item
        if getattr(item, "image_path", None):
            resolved = self._resolve_image_path(Path(item.image_path))
            if resolved:
                try:
                    img = pygame.image.load(str(resolved)).convert_alpha()
                    self.image_cache[item.name] = img
                    return img
                except pygame.error:
                    self.image_cache[item.name] = None
                    return None

        possible_names = [item.name, item.name.replace("/", "-")]
        search_roots = [self.assets_root, Path.cwd()]
        for base in possible_names:
            for ext in (".png", ".jpg", ".jpeg"):
                for root in search_roots:
                    path = root / "assets" / f"{base}{ext}"
                    if path.exists():
                        try:
                            img = pygame.image.load(str(path)).convert_alpha()
                            self.image_cache[item.name] = img
                            return img
                        except pygame.error:
                            self.image_cache[item.name] = None
                            return None

        self.image_cache[item.name] = None
        return None

    def update(self, dt: float):
        if self.episode.auction_done and self.stage != "sold":
            return

        self.bid_flash = max(0.0, self.bid_flash - dt)

        if not self.current_lot:
            self._prepare_next_lot()
            return

        self.stage_timer += dt

        if self.stage == "intro":
            if self.stage_timer >= 1.0:
                self.stage = "bidding"
                self.stage_timer = 0.0

        elif self.stage == "bidding":
            next_idx = self.current_bid_idx + 1
            if next_idx < len(self.bid_steps) and self.stage_timer >= self.bid_steps[next_idx]["time"]:
                self.current_bid_idx = next_idx
                step = self.bid_steps[next_idx]
                self.display_price = step["amount"]
                self.active_bidder = step["bidder"]
                self.bid_history.append(step)
                self.bid_flash = 0.35

            if self.stage_timer >= self.bid_total_duration:
                self.stage = "hammer"
                self.stage_timer = 0.0
                self.active_bidder = None

        elif self.stage == "hammer":
            if self.stage_timer >= 0.9:
                if self.hammer_idx < len(self.hammer_lines) - 1:
                    self.hammer_idx += 1
                    self.stage_timer = 0.0
                else:
                    self._finalize_sale()

        elif self.stage == "sold":
            if self.stage_timer >= self.sold_pause:
                self.current_lot = None
                self.stage = "idle"
                self.stage_timer = 0.0
                self.bid_history.clear()
                self.active_bidder = None

    def _render_background(self, surface, play_w):
        pygame.draw.rect(surface, INK, (0, 0, play_w, self.cfg.window_h))
        glow = pygame.Surface((play_w, self.cfg.window_h), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*ACCENT, 42), (0, 0, play_w, 120))
        pygame.draw.rect(glow, (*ACCENT, 22), (0, 140, play_w, 220))
        surface.blit(glow, (0, 0))

    def _render_header(self, surface):
        mood = self.episode.auction_house.mood.upper()
        draw_text(surface, f"Auction House ({mood})", 24, 18, self.big, TEXT)
        draw_text(surface, "Real bidders on the floor — pace slowed for drama", 24, 52, self.small, MUTED)

    def _render_stage(self, surface, rect):
        pygame.draw.rect(surface, CANVAS, rect, border_radius=18)
        floor_rect = (rect[0], rect[1] + rect[3] - 120, rect[2], 120)
        pygame.draw.rect(surface, self._shade(CANVAS, -10), floor_rect, border_radius=16)

        podium = pygame.Rect(rect[0] + rect[2] * 0.45, rect[1] + 14, 120, 64)
        pygame.draw.rect(surface, self._blend(CANVAS, ACCENT, 0.6), podium, border_radius=12)
        draw_text(surface, "Auctioneer", podium.x + 16, podium.y + 10, self.small, TEXT)
        draw_text(surface, self.episode.auctioneer.name, podium.x + 16, podium.y + 28, self.small, GOLD)

        price_y = rect[1] + 96
        price_label = f"Current bid" if self.stage != "sold" else "SOLD for"
        draw_text(surface, price_label, rect[0] + 20, price_y - 28, self.small, MUTED)
        price_color = GOOD if self.display_price >= (self.current_lot.item.shop_price if self.current_lot else 0) else BAD
        draw_text(surface, f"${self.display_price:,.0f}", rect[0] + 20, price_y, self.huge, price_color)

        callout = None
        if self.stage == "bidding" and self.active_bidder:
            callout = f"{self.active_bidder} bids ${self.display_price:,.0f}!"
        elif self.stage == "hammer":
            callout = self.hammer_lines[self.hammer_idx]
        elif self.stage == "sold":
            callout = "Going, going, gone!"
        if callout:
            draw_text(surface, callout, rect[0] + 20, price_y + 54, self.font, ACCENT)

        ticker_rect = pygame.Rect(rect[0] + rect[2] - 260, rect[1] + 16, 240, 96)

        self._render_crowd(surface, rect)
        self._render_bid_ticker(surface, ticker_rect)

    def _render_crowd(self, surface, rect):
        rows = [rect[1] + rect[3] - 80, rect[1] + rect[3] - 32]
        seats_per_row = 3
        spacing = rect[2] // (seats_per_row + 1)
        for ridx, row_y in enumerate(rows):
            for sidx in range(seats_per_row):
                bx = rect[0] + spacing * (sidx + 1)
                color = self._blend(CANVAS, ACCENT, 0.55)
                name_idx = ridx * seats_per_row + sidx
                label = self.bidder_names[name_idx % len(self.bidder_names)]
                highlight = label == self.active_bidder and self.stage != "sold"
                radius = 18 + (6 if highlight else 0)
                pygame.draw.circle(surface, self._shade(INK, 12), (bx, row_y + 6), radius + 6)
                pygame.draw.circle(surface, color if not highlight else ACCENT, (bx, row_y), radius)
                draw_text(surface, label, bx - 52, row_y + 22, self.small, MUTED)

        applause = None
        if self.stage == "sold":
            applause = "Audience applauds!"
        elif self.stage == "hammer":
            applause = "Hands poised..."
        if applause:
            draw_text(surface, applause, rect[0] + rect[2] - 180, rect[1] + rect[3] - 110, self.small, GOLD)

    def _render_bid_ticker(self, surface, rect: pygame.Rect):
        pygame.draw.rect(surface, PANEL, rect, border_radius=12)
        pygame.draw.rect(surface, PANEL_EDGE, rect, width=2, border_radius=12)
        draw_text(surface, "Bid history", rect.x + 12, rect.y + 10, self.small, MUTED)

        y = rect.y + 32
        last_entries = self.bid_history[-3:]
        for step in last_entries:
            bidder = step["bidder"]
            amt = step["amount"]
            highlight = bidder == self.active_bidder and self.bid_flash > 0
            col = ACCENT if highlight else TEXT
            draw_text(surface, f"{bidder} at ${amt:,.0f}", rect.x + 12, y, self.small, col)
            y += 18

    def _render_item_image(self, surface, rect, item):
        pygame.draw.rect(surface, PANEL, rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_EDGE, rect, width=2, border_radius=10)

        img = self._get_item_image(item)
        if img:
            padding = 10
            max_side = max(1, min(rect.width, rect.height) - padding * 2)
            scale = min(max_side / img.get_width(), max_side / img.get_height())
            scaled_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            scaled = pygame.transform.smoothscale(img, scaled_size)
            pos = (
                rect.x + (rect.width - scaled_size[0]) // 2,
                rect.y + (rect.height - scaled_size[1]) // 2,
            )
            surface.blit(scaled, pos)
        else:
            draw_text(surface, "Image spot", rect.x + 10, rect.y + 10, self.small, MUTED)
            draw_text(surface, item.name[:28], rect.x + 10, rect.y + 34, self.small, TEXT)

    def _render_lot_panel(self, surface, x, y, w, title, lot):
        image_size = min(w - 24, 120)
        text_block_height = 96
        panel_height = image_size + 42 + text_block_height
        panel_rect = (x, y, w, panel_height)
        draw_panel(surface, panel_rect)
        draw_text(surface, title, x + 12, y + 12, self.font, GOLD)

        img_rect = pygame.Rect(x + 12, y + 42, image_size, image_size)
        if not lot:
            pygame.draw.rect(surface, PANEL, img_rect, border_radius=10)
            pygame.draw.rect(surface, PANEL_EDGE, img_rect, width=2, border_radius=10)
            draw_text(surface, "Image spot", img_rect.x + 10, img_rect.y + 10, self.small, MUTED)
            draw_text(surface, "Awaiting lot...", img_rect.x + 10, img_rect.y + 34, self.small, TEXT)
            draw_text(surface, "Keep the pace — more bidders coming soon", x + 12, img_rect.bottom + 14, self.small, MUTED)
            return panel_height

        self._render_item_image(surface, img_rect, lot.item)

        text_y = img_rect.bottom + 14
        tag = " [EXPERT]" if lot.item.is_expert_pick else ""
        draw_text(surface, f"{lot.team.name}{tag}", x + 12, text_y, self.small, lot.team.color); text_y += 18
        draw_text(surface, f"{lot.item.name}", x + 12, text_y, self.small, TEXT); text_y += 18
        draw_text(surface, f"Paid ${lot.item.shop_price:.0f}  |  Appraised ${lot.item.appraised_value:.0f}", x + 12, text_y, self.small, MUTED); text_y += 18
        draw_text(surface, f"Category: {lot.item.category}  •  Condition {lot.item.condition*100:0.0f}%", x + 12, text_y, self.small, MUTED)
        return panel_height

    def _render_last_sale(self, surface, x, y, w):
        if not self.episode.last_sold:
            return
        lot = self.episode.last_sold
        draw_text(surface, "Last hammer fall", x, y, self.small, GOLD); y += 18
        profit = lot.item.auction_price - lot.item.shop_price
        col = GOOD if profit > 0 else BAD
        draw_text(surface, f"{lot.item.name} sold for ${lot.item.auction_price:.0f} (Δ {profit:+.0f})", x, y, self.small, col)

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        self._render_background(surface, play_w)
        self._render_header(surface)

        stage_rect = (self.cfg.margin, 90, play_w - self.cfg.margin * 3 - 220, self.cfg.window_h - 160)
        stage_rect = pygame.Rect(stage_rect)
        stage_rect.width = max(320, stage_rect.width)
        self._render_stage(surface, stage_rect)

        side_x = stage_rect.x + stage_rect.width + 16
        side_w = play_w - side_x - self.cfg.margin
        now_h = self._render_lot_panel(surface, side_x, stage_rect.y, side_w, "Now selling", self.current_lot)
        gap = 20
        up_next_y = stage_rect.y + now_h + gap
        next_h = self._render_lot_panel(surface, side_x, up_next_y, side_w, "Up next", self._peek_next_lot())
        self._render_last_sale(surface, side_x, up_next_y + next_h + gap * 2, side_w)

        # progress bar
        total = len(self.episode.auction_queue)
        cur = self.episode.auction_cursor + (1 if self.stage != "idle" and not self.episode.auction_done else 0)
        draw_text(surface, f"Progress: {cur}/{total}", stage_rect.x, self.cfg.window_h - 46, self.small, MUTED)
        bar_w = stage_rect.width
        pygame.draw.rect(surface, PANEL_EDGE, (stage_rect.x, self.cfg.window_h - 30, bar_w, 12), border_radius=6)
        if total:
            filled = bar_w * (cur / total)
            pygame.draw.rect(surface, ACCENT, (stage_rect.x, self.cfg.window_h - 30, filled, 12), border_radius=6)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "AUCTION",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
