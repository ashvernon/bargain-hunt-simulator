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
from ui.screens.expert_budget_screen import ExpertBudgetScreen
from ui.screens.expert_shopping_screen import ExpertShoppingScreen
from ui.screens.expert_reveal_screen import ExpertRevealScreen
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
            expert_min_budget=cfg.expert_min_budget,
            cfg=cfg,
        )
        self.episode.setup()
        self.episode.time_scale = self.time_scale

        self.market_time_left = cfg.market_seconds
        self.expert_budget_reserved = False

        self.screens = {
            "INTRO_HOST": HostWelcomeScreen(cfg),
            "INTRO_CONTESTANTS": ContestantIntroScreen(cfg, self.episode),
            "INTRO_EXPERTS": ExpertAssignmentScreen(cfg, self.episode),
            "INTRO_MARKET": MarketSendoffScreen(cfg),
            "MARKET": MarketScreen(cfg, self.episode),
            "EXPERT_HANDOFF": ExpertBudgetScreen(cfg, self.episode),
            "EXPERT_SHOPPING": ExpertShoppingScreen(cfg, self.episode),
            "EXPERT_REVEAL": ExpertRevealScreen(cfg, self.episode),
            "APPRAISAL": AppraisalScreen(cfg, self.episode),
            "AUCTION_TEAM": AuctionScreen(cfg, self.episode),
            "AUCTION_EXPERT": AuctionScreen(cfg, self.episode),
            "RESULTS": ResultsScreen(cfg, self.episode),
        }
        self.screen = self.screens[self.phase]
        if hasattr(self.screen, "reset"):
            self.screen.reset()

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
            self.episode.update_market_ai(dt, cfg=self.cfg)
            self.screen.update(dt)
            self.screen.set_time_left(self.market_time_left)

            if self.market_time_left <= 0 or self._market_shopping_done():
                self.market_time_left = min(self.market_time_left, 0)
                self._enter_expert_handoff_phase()

        elif self.phase in ("EXPERT_HANDOFF", "EXPERT_SHOPPING"):
            self.screen.update(dt)
            if getattr(self.screen, "is_done", False):
                self._advance_phase()

        elif self.phase == "APPRAISAL":
            if not self.episode.appraisal_done:
                self.episode.start_appraisal()
            self._advance_phase()

        elif self.phase in ("AUCTION_TEAM", "AUCTION_EXPERT"):
            self.screen.update(dt)
            if self.episode.auction_done:
                self._advance_phase()

        elif self.phase == "EXPERT_REVEAL":
            self.screen.update(dt)
            if getattr(self.screen, "decisions_complete", lambda: False)():
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
            self._enter_expert_handoff_phase()
            return
        elif self.phase == "EXPERT_HANDOFF":
            self._enter_expert_shopping_phase()
            return
        elif self.phase == "EXPERT_SHOPPING":
            self.phase = "APPRAISAL"
        elif self.phase == "APPRAISAL":
            self.phase = "AUCTION_TEAM"
            self.episode.start_team_auction()
            self.screens["AUCTION_TEAM"].reset_for_new_queue()
        elif self.phase == "AUCTION_TEAM":
            self.phase = "EXPERT_REVEAL"
        elif self.phase == "EXPERT_REVEAL":
            if self.episode.has_included_expert_items():
                self.phase = "AUCTION_EXPERT"
                self.episode.start_expert_auction()
                self.screens["AUCTION_EXPERT"].reset_for_new_queue()
            else:
                self.phase = "RESULTS"
                self.episode.compute_results()
        elif self.phase == "AUCTION_EXPERT":
            self.phase = "RESULTS"
            self.episode.compute_results()

        self.screen = self.screens[self.phase]
        if hasattr(self.screen, "reset"):
            self.screen.reset()

    def _enter_expert_handoff_phase(self):
        if not self.expert_budget_reserved:
            self.episode.reserve_expert_budget()
            self.expert_budget_reserved = True
        self.phase = "EXPERT_HANDOFF"
        self.screen = self.screens[self.phase]
        if hasattr(self.screen, "reset"):
            self.screen.reset()

    def _enter_expert_shopping_phase(self):
        self.episode.prepare_expert_picks()
        self.phase = "EXPERT_SHOPPING"
        self.screen = self.screens[self.phase]
        if hasattr(self.screen, "reset"):
            self.screen.reset()

    def _market_shopping_done(self) -> bool:
        return all(len(team.team_items) >= self.cfg.items_per_team for team in self.episode.teams)

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
