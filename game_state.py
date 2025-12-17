import pygame
from config import GameConfig
from sim.item_factory import configure_item_factory
from ui.screens.market_screen import MarketScreen
from ui.screens.intro_screens import (
    HostWelcomeScreen,
    ContestantIntroScreen,
    ExpertAssignmentScreen,
    MarketSendoffScreen,
)
from ui.screens.expert_decision_screen import ExpertDecisionScreen
from ui.screens.appraisal_screen import AppraisalScreen
from ui.screens.auction_screen import AuctionScreen
from ui.screens.results_screen import ResultsScreen

class GameState:
    def __init__(self, cfg: GameConfig, seed: int, episode_idx: int):
        self.cfg = cfg
        self.intro_enabled = cfg.show_host_intro
        self.phase = "INTRO_HOST" if self.intro_enabled else "MARKET"
        self.time_scale = 1.0
        play_rect = (0, 0, cfg.window_w - cfg.hud_w, cfg.window_h)

        # Configure which item dataset should be used for this run before
        # any items are generated.
        configure_item_factory(cfg.item_source)

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
            "INTRO_HOST": HostWelcomeScreen(cfg),
            "INTRO_CONTESTANTS": ContestantIntroScreen(cfg, self.episode),
            "INTRO_EXPERTS": ExpertAssignmentScreen(cfg, self.episode),
            "INTRO_MARKET": MarketSendoffScreen(cfg),
            "MARKET": MarketScreen(cfg, self.episode),
            "EXPERT_DECISION": ExpertDecisionScreen(cfg, self.episode),
            "APPRAISAL": AppraisalScreen(cfg, self.episode),
            "AUCTION": AuctionScreen(cfg, self.episode),
            "RESULTS": ResultsScreen(cfg, self.episode),
        }
        self.screen = self.screens[self.phase]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.phase.startswith("INTRO"):
                if event.key == pygame.K_SPACE:
                    self._skip_intro_sequence()
                    return
                if event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                    self._advance_phase()
                    return
            elif event.key == pygame.K_SPACE:
                # Skip forward quickly
                self._advance_phase(force=True)
            elif event.key == pygame.K_f:
                self._toggle_speed()
        self.screen.handle_event(event)

    def update(self, dt: float):
        if self.phase.startswith("INTRO"):
            return

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
        if self.phase.startswith("INTRO"):
            self._advance_intro_sequence()
            return
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
        speeds = [2.0, 10.0, 20.0]
        try:
            idx = speeds.index(self.time_scale)
        except ValueError:
            idx = 0
        self.time_scale = speeds[(idx + 1) % len(speeds)]
        self.episode.time_scale = self.time_scale

    def render(self, screen):
        self.episode.time_scale = self.time_scale
        self.screen.render(screen)

    def _advance_intro_sequence(self):
        intro_flow = ["INTRO_HOST", "INTRO_CONTESTANTS", "INTRO_EXPERTS", "INTRO_MARKET"]
        if self.phase not in intro_flow:
            return
        idx = intro_flow.index(self.phase)
        if idx < len(intro_flow) - 1:
            self.phase = intro_flow[idx + 1]
        else:
            self.phase = "MARKET"
        self.screen = self.screens[self.phase]

    def _skip_intro_sequence(self):
        if not self.phase.startswith("INTRO"):
            return
        self.phase = "MARKET"
        self.screen = self.screens[self.phase]
