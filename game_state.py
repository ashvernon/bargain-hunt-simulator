import pygame
from config import GameConfig
from ui.screens.market_screen import MarketScreen
from ui.screens.expert_decision_screen import ExpertDecisionScreen
from ui.screens.appraisal_screen import AppraisalScreen
from ui.screens.auction_screen import AuctionScreen
from ui.screens.results_screen import ResultsScreen

class GameState:
    def __init__(self, cfg: GameConfig, seed: int, episode_idx: int):
        self.cfg = cfg
        self.phase = "MARKET"
        self.time_scale = 1.0
        play_rect = (0, 0, cfg.window_w - cfg.hud_w, cfg.window_h)
        from models.episode import Episode
        self.episode = Episode(
            ep_idx=episode_idx,
            seed=seed,
            play_rect=play_rect,
            items_per_team=cfg.items_per_team,
            starting_budget=cfg.starting_budget,
        )
        self.episode.setup()
        self.episode.time_scale = self.time_scale

        self.market_time_left = cfg.market_seconds
        self.expert_decision_started = False

        self.screens = {
            "MARKET": MarketScreen(cfg, self.episode),
            "EXPERT_DECISION": ExpertDecisionScreen(cfg, self.episode),
            "APPRAISAL": AppraisalScreen(cfg, self.episode),
            "AUCTION": AuctionScreen(cfg, self.episode),
            "RESULTS": ResultsScreen(cfg, self.episode),
        }
        self.screen = self.screens[self.phase]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Skip forward quickly
                self._advance_phase(force=True)
            elif event.key == pygame.K_f:
                self._toggle_speed()
        self.screen.handle_event(event)

    def update(self, dt: float):
        dt *= self.time_scale
        if self.phase == "MARKET":
            self.market_time_left -= dt
            self.episode.update_market_ai(dt, self.cfg.team_speed_px_s, self.cfg.buy_radius_px)
            self.screen.set_time_left(self.market_time_left)

            if self.market_time_left <= 0 or self._market_shopping_done():
                self.market_time_left = min(self.market_time_left, 0)
                # expert leftover purchase
                self._enter_expert_decision_phase()

        elif self.phase == "EXPERT_DECISION":
            self.screen.update(dt)
            if self.episode.expert_purchases_done():
                self._advance_phase()

        elif self.phase == "APPRAISAL":
            if not self.episode.appraisal_done:
                self.episode.start_appraisal()
            self._advance_phase()

        elif self.phase == "AUCTION":
            self.screen.update(dt)
            if self.episode.auction_done:
                self._advance_phase()

        elif self.phase == "RESULTS":
            pass

    def _advance_phase(self, force=False):
        if self.phase == "MARKET":
            if force:
                self.market_time_left = 0
            self._enter_expert_decision_phase()
            return
        elif self.phase == "EXPERT_DECISION":
            if not self.episode.expert_purchases_done():
                return
            self.phase = "APPRAISAL"
        elif self.phase == "APPRAISAL":
            self.phase = "AUCTION"
            self.episode.start_auction()
        elif self.phase == "AUCTION":
            self.phase = "RESULTS"
            self.episode.compute_results()

        self.screen = self.screens[self.phase]

    def _enter_expert_decision_phase(self):
        if not self.expert_decision_started:
            self.episode.finish_market_expert_leftover_purchase()
            self.expert_decision_started = True
        self.phase = "EXPERT_DECISION"
        self.screen = self.screens[self.phase]
        # reset the decision cursor now that new proposals exist
        if hasattr(self.screen, "cursor"):
            self.screen.cursor = 0
            if hasattr(self.screen, "_sync_cursor"):
                self.screen._sync_cursor()

    def _market_shopping_done(self) -> bool:
        remaining = list(self.episode.market.all_remaining_items())
        if not remaining:
            return True

        min_price = min(it.shop_price for it in remaining)
        teams_complete = []
        for team in self.episode.teams:
            team_items = [i for i in team.items_bought if not i.is_expert_pick]
            filled = len(team_items) >= self.cfg.items_per_team
            broke = team.budget_left < min_price
            teams_complete.append(filled or broke)
        return all(teams_complete)

    def _toggle_speed(self):
        speeds = [1.0, 3.0, 8.0]
        try:
            idx = speeds.index(self.time_scale)
        except ValueError:
            idx = 0
        self.time_scale = speeds[(idx + 1) % len(speeds)]
        self.episode.time_scale = self.time_scale

    def render(self, screen):
        self.episode.time_scale = self.time_scale
        self.screen.render(screen)
