import pygame
from config import GameConfig
from ui.screens.market_screen import MarketScreen
from ui.screens.appraisal_screen import AppraisalScreen
from ui.screens.auction_screen import AuctionScreen
from ui.screens.results_screen import ResultsScreen

class GameState:
    def __init__(self, cfg: GameConfig, seed: int, episode_idx: int):
        self.cfg = cfg
        self.phase = "MARKET"
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

        self.market_time_left = cfg.market_seconds

        self.screens = {
            "MARKET": MarketScreen(cfg, self.episode),
            "APPRAISAL": AppraisalScreen(cfg, self.episode),
            "AUCTION": AuctionScreen(cfg, self.episode),
            "RESULTS": ResultsScreen(cfg, self.episode),
        }
        self.screen = self.screens[self.phase]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            # Skip forward quickly
            self._advance_phase(force=True)
        self.screen.handle_event(event)

    def update(self, dt: float):
        if self.phase == "MARKET":
            self.market_time_left -= dt
            self.episode.update_market_ai(dt, self.cfg.team_speed_px_s, self.cfg.buy_radius_px)
            self.screen.set_time_left(self.market_time_left)

            if self.market_time_left <= 0:
                # expert leftover purchase
                self.episode.finish_market_expert_leftover_purchase()
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
            self.phase = "APPRAISAL"
        elif self.phase == "APPRAISAL":
            self.phase = "AUCTION"
            self.episode.start_auction()
        elif self.phase == "AUCTION":
            self.phase = "RESULTS"
            self.episode.compute_results()

        self.screen = self.screens[self.phase]

    def render(self, screen):
        self.screen.render(screen)
