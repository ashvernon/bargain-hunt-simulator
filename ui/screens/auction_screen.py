import random
from pathlib import Path
import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text, draw_panel
from ui.screens.components.auction_summary_panel import render_auction_summary_panel
from models.auction_result import AuctionRoundResult
from constants import TEXT, MUTED, GOOD, BAD, GOLD, ACCENT, INK, CANVAS, PANEL, PANEL_EDGE


class AuctionScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 18)
        self.big = pygame.font.SysFont(None, 34)
        self.huge = pygame.font.SysFont(None, 48)
        self.status_font = pygame.font.SysFont(None, 20)

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
        self.placeholder_cache: dict[str, pygame.Surface] = {}
        self.assets_root = Path(__file__).resolve().parent.parent.parent

        self.flow_state = "selling"
        self.summary_timer = 0.0
        self.summary_duration = 4.0
        self.allow_summary_skip = True
        self.summary_result: AuctionRoundResult | None = None
        self.hold_final_done = False
        self.current_team = None
        self.visual_rng: random.Random | None = None

        self.bidder_names = [
            "Gallery rep",
            "Local dealer",
            "Phone bidder",
            "Online proxy",
            "Vintage scout",
            "Museum intern",
        ]
        self.hammer_lines = ["Going once...", "Going twice...", "Final call..."]

    def reset_for_new_queue(self):
        self.stage = "idle"
        self.stage_timer = 0.0
        self.display_price = 0.0
        self.current_lot = None
        self.pending_sale_price = 0.0
        self.bid_history.clear()
        self.bid_steps = []
        self.bid_total_duration = 0.0
        self.current_bid_idx = -1
        self.active_bidder = None
        self.bid_flash = 0.0
        self.hammer_idx = 0
        self.episode.last_sold = None
        self.flow_state = "selling"
        self.summary_timer = 0.0
        self.summary_result = None
        self.hold_final_done = False
        self.current_team = None
        self.visual_rng = None

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

        stage_code = 0 if self.episode.auction_stage == "team" else 1
        visual_seed = self.episode.seed * 1_000_003 + stage_code * 10_000 + self.episode.auction_cursor
        self.visual_rng = random.Random(visual_seed)

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
        self.current_team = lot.team
        self.hammer_idx = 0
        self.bid_history.clear()

    def _build_bid_script(self, start_price: float, sale_price: float):
        rng = self.visual_rng or random.Random()
        steps = []
        time_cursor = 0.7
        bids = rng.randint(3, 6)
        chosen_bidders = [rng.choice(self.bidder_names) for _ in range(bids)]

        for idx in range(bids):
            bidder = chosen_bidders[idx]
            fraction = (idx + 1) / bids
            reach = start_price + (sale_price - start_price) * (0.55 + 0.45 * fraction)
            reach = min(sale_price, reach)
            steps.append({"time": time_cursor, "amount": reach, "bidder": bidder})
            time_cursor += rng.uniform(0.85, 1.15)

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

    def _team_finished(self, team) -> bool:
        for idx in range(self.episode.auction_cursor, len(self.episode.auction_queue)):
            if self.episode.auction_queue[idx].team == team:
                return False
        return True

    def _items_for_round(self, team):
        if self.episode.auction_stage == "team":
            return [lot.item for lot in self.episode.auction_queue if lot.team == team]
        if self.episode.auction_stage == "expert" and team.expert_pick_included and team.expert_pick_item:
            return [team.expert_pick_item]
        return []

    def _team_round_progress(self, team):
        lots = [lot for lot in self.episode.auction_queue if lot.team == team]
        sold = sum(1 for lot in lots if getattr(lot.item, "auction_price", 0) > 0)
        return sold, len(lots)

    def _enter_summary(self, team):
        items = self._items_for_round(team)
        if not items:
            return
        self.summary_result = AuctionRoundResult.from_team(team, items)
        self.summary_timer = 0.0
        self.flow_state = "summary"
        self.hold_final_done = self.episode.auction_done
        if self.hold_final_done:
            self.episode.auction_done = False

    def _exit_summary(self):
        self.flow_state = "selling"
        self.summary_timer = 0.0
        self.summary_result = None
        if self.hold_final_done:
            self.episode.auction_done = True
            self.hold_final_done = False
        if not self.current_lot:
            self._prepare_next_lot()

    def _resolve_image_path(self, candidate: Path) -> Path | None:
        """Resolve an image path whether the game is launched from the repo root or elsewhere."""
        if candidate.is_absolute():
            return candidate if candidate.exists() else None

        for root in (Path.cwd(), self.assets_root):
            path = root / candidate
            if path.exists():
                return path
        return None

    def _get_item_image(self, name: str, image_path: str | None = None):
        cache_key = image_path or name
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        candidate_path = Path(image_path) if image_path else None
        if candidate_path:
            resolved = self._resolve_image_path(candidate_path)
            if resolved:
                try:
                    img = pygame.image.load(str(resolved)).convert_alpha()
                    self.image_cache[cache_key] = img
                    return img
                except pygame.error:
                    self.image_cache[cache_key] = None
                    return None

        possible_names = [name, name.replace("/", "-")]
        search_roots = [self.assets_root, Path.cwd()]
        for base in possible_names:
            for ext in (".png", ".jpg", ".jpeg"):
                for root in search_roots:
                    path = root / "assets" / f"{base}{ext}"
                    if path.exists():
                        try:
                            img = pygame.image.load(str(path)).convert_alpha()
                            self.image_cache[cache_key] = img
                            return img
                        except pygame.error:
                            self.image_cache[cache_key] = None
                            return None

        self.image_cache[cache_key] = None
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.flow_state == "summary" and self.allow_summary_skip:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._exit_summary()

    def _placeholder_surface(self, category: str) -> pygame.Surface:
        if category in self.placeholder_cache:
            return self.placeholder_cache[category]

        surface = pygame.Surface((80, 80), pygame.SRCALPHA)
        tint_weight = 0.25 + (abs(hash(category)) % 30) / 100
        tone = self._blend(CANVAS, ACCENT, tint_weight)
        pygame.draw.rect(surface, tone, (6, 6, 68, 68), border_radius=16)
        pygame.draw.rect(surface, PANEL_EDGE, (6, 6, 68, 68), width=2, border_radius=16)
        pygame.draw.circle(surface, self._shade(tone, 24), (40, 36), 16)
        pygame.draw.rect(surface, self._shade(tone, -14), (22, 44, 36, 18), border_radius=6)
        draw_text(surface, category[:6].title(), 10, 60, self.small, MUTED)

        self.placeholder_cache[category] = surface
        return surface

    def _render_thumbnail(self, surface, rect, name: str, category: str, image_path: str | None = None, with_frame: bool = True):
        if with_frame:
            pygame.draw.rect(surface, PANEL, rect, border_radius=10)
            pygame.draw.rect(surface, PANEL_EDGE, rect, width=2, border_radius=10)

        img = self._get_item_image(name, image_path)
        if img:
            padding = 8
            max_side = max(1, min(rect.width, rect.height) - padding * 2)
            scale = min(max_side / img.get_width(), max_side / img.get_height())
            scaled_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            scaled = pygame.transform.smoothscale(img, scaled_size)
            pos = (
                rect.x + (rect.width - scaled_size[0]) // 2,
                rect.y + (rect.height - scaled_size[1]) // 2,
            )
            surface.blit(scaled, pos)
            return

        placeholder = self._placeholder_surface(category or "item")
        padding = 6
        max_side = max(1, min(rect.width, rect.height) - padding * 2)
        scaled = pygame.transform.smoothscale(placeholder, (max_side, max_side))
        pos = (rect.x + (rect.width - max_side) // 2, rect.y + (rect.height - max_side) // 2)
        surface.blit(scaled, pos)

    def update(self, dt: float):
        if self.flow_state == "summary":
            self.summary_timer += dt
            if self.summary_timer >= self.summary_duration:
                self._exit_summary()
            return

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
                finished_team = self.current_lot.team if self.current_lot else None
                self.current_lot = None
                self.stage = "idle"
                self.stage_timer = 0.0
                self.bid_history.clear()
                self.active_bidder = None
                if finished_team and self._team_finished(finished_team):
                    self._enter_summary(finished_team)
                    return

    def _render_background(self, surface, play_w):
        pygame.draw.rect(surface, INK, (0, 0, play_w, self.cfg.window_h))
        glow = pygame.Surface((play_w, self.cfg.window_h), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*ACCENT, 42), (0, 0, play_w, 120))
        pygame.draw.rect(glow, (*ACCENT, 22), (0, 140, play_w, 220))
        surface.blit(glow, (0, 0))

    def _render_header(self, surface):
        mood = self.episode.auction_house.mood.upper()
        draw_text(surface, f"Auction House ({mood})", 24, 18, self.big, TEXT)
        draw_text(surface, "Show-style pacing, one team at a time", 24, 52, self.small, MUTED)
        draw_text(surface, "Round recaps roll between teams", 24, 76, self.small, GOLD)

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
            col = ACCENT if self.stage != "sold" else GOLD
            font = self.font if self.stage != "sold" else self.status_font
            draw_text(surface, callout, rect[0] + 20, price_y + 54, font, col)

        ticker_rect = pygame.Rect(rect[0] + rect[2] - 260, rect[1] + 16, 240, 96)

        self._render_crowd(surface, rect)
        self._render_bid_ticker(surface, ticker_rect)

    def _render_crowd(self, surface, rect):
        row_y = rect[1] + rect[3] - 46
        seats = 6
        spacing = rect[2] // (seats + 1)
        for sidx in range(seats):
            bx = rect[0] + spacing * (sidx + 1)
            color = self._blend(CANVAS, ACCENT, 0.55)
            label = self.bidder_names[sidx % len(self.bidder_names)]
            highlight = label == self.active_bidder and self.stage != "sold"
            radius = 14 + (5 if highlight else 0)
            pygame.draw.circle(surface, self._shade(INK, 12), (bx, row_y + 4), radius + 4)
            pygame.draw.circle(surface, color if not highlight else ACCENT, (bx, row_y), radius)
        applause = None
        if self.stage == "sold":
            applause = "Audience applauds!"
        elif self.stage == "hammer":
            applause = "Hands poised..."
        if applause:
            draw_text(surface, applause, rect[0] + 18, row_y - 26, self.small, GOLD)

    def _render_bid_ticker(self, surface, rect: pygame.Rect):
        pygame.draw.rect(surface, PANEL, rect, border_radius=12)
        pygame.draw.rect(surface, PANEL_EDGE, rect, width=2, border_radius=12)
        draw_text(surface, "Bid history", rect.x + 12, rect.y + 10, self.small, MUTED)

        y = rect.y + 32
        last_entries = self.bid_history[-6:]
        if not last_entries:
            draw_text(surface, "Waiting for bids...", rect.x + 12, y, self.small, MUTED)
            return

        for idx, step in enumerate(last_entries):
            bidder = step["bidder"]
            amt = step["amount"]
            highlight = bidder == self.active_bidder and self.bid_flash > 0
            col = ACCENT if highlight else TEXT
            draw_text(surface, f"{bidder} at ${amt:,.0f}", rect.x + 12, y, self.small, col)
            y += 18
            if idx < len(last_entries) - 1:
                pygame.draw.line(surface, self._shade(PANEL_EDGE, -10), (rect.x + 8, y), (rect.right - 8, y), width=1)
                y += 6

    def _render_item_image(self, surface, rect, item):
        self._render_thumbnail(surface, rect, item.name, item.category, getattr(item, "image_path", None))

    def _render_lot_panel(self, surface, x, y, w, title, lot, compact: bool = False):
        image_cap = 110 if not compact else 80
        image_size = min(w - 24, image_cap)
        text_block_height = 82 if not compact else 54
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
        draw_text(surface, f"Lot {lot.position_in_team}/{lot.team_total}: {lot.item.name}", x + 12, text_y, self.small, TEXT); text_y += 18
        draw_text(surface, f"Paid ${lot.item.shop_price:.0f}  |  Appraised ${lot.item.appraised_value:.0f}", x + 12, text_y, self.small, MUTED); text_y += 18
        if not compact:
            draw_text(surface, f"Category: {lot.item.category}  •  Condition {lot.item.condition*100:0.0f}%", x + 12, text_y, self.small, MUTED)
        return panel_height

    def _render_last_sale(self, surface, x, y, w):
        if not self.episode.last_sold:
            return
        lot = self.episode.last_sold
        panel_height = 70
        panel_rect = pygame.Rect(x, y, w, panel_height)
        draw_panel(surface, panel_rect)

        text_x = panel_rect.x + 12
        text_y = panel_rect.y + 10
        draw_text(surface, "Last hammer fall", text_x, text_y, self.small, GOLD); text_y += 22

        profit = lot.item.auction_price - lot.item.shop_price
        col = GOOD if profit > 0 else BAD
        draw_text(surface, f"{lot.item.name}", text_x, text_y, self.small, TEXT); text_y += 18
        draw_text(surface, f"SOLD for ${lot.item.auction_price:.0f}  (Δ {profit:+.0f})", text_x, text_y, self.small, col)

    def _render_status_strip(self, surface, stage_rect):
        strip_rect = pygame.Rect(stage_rect.x, self.cfg.window_h - 48, stage_rect.width, 30)
        pygame.draw.rect(surface, PANEL, strip_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_EDGE, strip_rect, width=2, border_radius=10)

        phase_label = "Team auction" if self.episode.auction_stage == "team" else "Expert auction"
        draw_text(surface, phase_label, strip_rect.x + 10, strip_rect.y + 6, self.status_font, MUTED)
        draw_text(surface, self.episode.auction_label, strip_rect.x + 180, strip_rect.y + 6, self.status_font, TEXT)

        total = len(self.episode.auction_queue)
        cur = self.episode.auction_cursor + (1 if self.stage != "idle" and not self.episode.auction_done else 0)
        progress_label = f"{cur}/{total} lots"
        draw_text(surface, progress_label, strip_rect.right - 110, strip_rect.y + 6, self.status_font, MUTED)

        bar_rect = pygame.Rect(strip_rect.x + 10, strip_rect.bottom - 10, strip_rect.width - 20, 6)
        pygame.draw.rect(surface, PANEL_EDGE, bar_rect, width=1, border_radius=4)
        if total:
            filled = bar_rect.width * (cur / total)
            pygame.draw.rect(surface, ACCENT, (bar_rect.x, bar_rect.y, filled, bar_rect.height), border_radius=4)

    def _render_team_focus(self, surface, x, y, w):
        panel_height = 94
        rect = pygame.Rect(x, y, w, panel_height)
        draw_panel(surface, rect)
        team = self.current_team or (self.current_lot.team if self.current_lot else None) or (self._peek_next_lot().team if self._peek_next_lot() else None)
        if not team:
            draw_text(surface, "Awaiting next team", rect.x + 12, rect.y + 12, self.font, MUTED)
            draw_text(surface, "Standby for the next lots to enter the hall", rect.x + 12, rect.y + 36, self.small, MUTED)
            return panel_height

        sold, total = self._team_round_progress(team)
        draw_text(surface, f"{team.name} team spotlight", rect.x + 12, rect.y + 10, self.font, team.color)
        draw_text(surface, f"Confidence {team.average_confidence*100:0.0f}% • Taste {team.average_taste*100:0.0f}%", rect.x + 12, rect.y + 34, self.small, MUTED)

        budget = f"Budget left ${team.budget_left:,.0f}"
        progress = f"Sold {sold}/{total} • Items remaining {max(total - sold, 0)}"
        draw_text(surface, budget, rect.x + 12, rect.y + 54, self.small, TEXT)
        draw_text(surface, progress, rect.x + 12, rect.y + 72, self.small, MUTED)
        return panel_height

    def _render_summary_overlay(self, surface, play_w):
        if not self.summary_result:
            return
        veil = pygame.Surface((play_w, self.cfg.window_h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        surface.blit(veil, (0, 0))

        panel_rect = pygame.Rect(
            self.cfg.margin * 2,
            120,
            play_w - self.cfg.margin * 4,
            self.cfg.window_h - 200,
        )
        fonts = {
            "title": self.big,
            "body": self.font,
            "small": self.small,
        }
        render_auction_summary_panel(
            surface,
            panel_rect,
            self.summary_result,
            fonts,
            lambda surf, rect, lot: self._render_thumbnail(
                surf,
                rect,
                lot.name,
                lot.category,
                lot.image_path,
                with_frame=False,
            ),
        )
        hint = "Space/Enter to continue" if self.allow_summary_skip else "Advancing shortly..."
        draw_text(surface, hint, panel_rect.x + 6, panel_rect.bottom + 10, self.small, MUTED)

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
        focus_h = self._render_team_focus(surface, side_x, stage_rect.y, side_w)
        gap = 12
        now_h = self._render_lot_panel(surface, side_x, stage_rect.y + focus_h + gap, side_w, "Now selling", self.current_lot)
        up_next_y = stage_rect.y + focus_h + gap + now_h + gap
        next_h = self._render_lot_panel(surface, side_x, up_next_y, side_w, "Up next", self._peek_next_lot(), compact=True)
        self._render_last_sale(surface, side_x, up_next_y + next_h + gap, side_w)

        self._render_status_strip(surface, stage_rect)

        if self.flow_state == "summary" and self.summary_result:
            self._render_summary_overlay(surface, play_w)

        phase_label = "AUCTION_TEAM" if self.episode.auction_stage == "team" else "AUCTION_EXPERT"
        render_hud(
            surface,
            self.cfg,
            self.episode,
            phase_label,
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
