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
        self.state = "pitch"  # pitch -> decision -> host_reveal
        self.phase_timer = 0.0
        self.pitch_duration = 2.8
        self.reveal_delay = 1.6
        self.post_reveal_delay = 2.2
        self.decision_reason = ""
        self.auto_score = 0.0
        self.active_team = None
        self.active_pick = None

    def reset(self):
        self.choice_include = True
        self.cursor = 0
        self.is_done = False
        self.state = "pitch"
        self.phase_timer = 0.0
        self.decision_reason = ""
        self.auto_score = 0.0
        self.active_team = None
        self.active_pick = None
        self._sync_cursor()

    def _pending_teams(self):
        return [t for t in self.episode.teams if t.expert_pick_item and t.expert_pick_included is None]

    def _sync_cursor(self):
        pending = self._pending_teams()
        if not pending:
            if not self.active_team:
                self.is_done = True
            return
        self.is_done = False
        self.cursor = 0
        self.active_team = pending[0]
        self.active_pick = self.active_team.expert_pick_item
        self.choice_include = self._default_choice(self.active_team)
        self.state = "pitch"
        self.phase_timer = 0.0
        self.decision_reason = ""
        self.auto_score = 0.0

    def _default_choice(self, team):
        pick = team.expert_pick_item
        if not pick:
            return False
        estimate = pick.attributes.get("expert_estimate", pick.shop_price)
        return (estimate - pick.shop_price) >= 2.0

    def decisions_complete(self) -> bool:
        return self.is_done

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.is_done:
            return

        # Keys now just fast-forward through the automated beats
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.state == "pitch":
                self._automate_choice(self.active_team)
            elif self.state == "decision":
                self._advance_to_host_reveal()
            elif self.state == "host_reveal":
                self._advance_to_next_team()

    def _advance_to_host_reveal(self):
        self.state = "host_reveal"
        self.phase_timer = 0.0

    def _advance_to_next_team(self):
        self.active_team = None
        self.active_pick = None
        self._sync_cursor()

    def update(self, dt: float):
        if self.is_done:
            return
        self.phase_timer += dt
        if not self.active_team:
            self._sync_cursor()
        if not self.active_team:
            self.is_done = True
            return

        if self.state == "pitch" and self.phase_timer >= self.pitch_duration:
            self._automate_choice(self.active_team)
        elif self.state == "decision" and self.phase_timer >= self.reveal_delay:
            self._advance_to_host_reveal()
        elif self.state == "host_reveal" and self.phase_timer >= self.post_reveal_delay:
            self._advance_to_next_team()

    def _performance_signal(self, team) -> float:
        margins = []
        for it in team.team_items:
            if it.auction_price is None:
                continue
            margins.append((it.auction_price - it.shop_price) / max(1.0, it.shop_price))
        if not margins:
            return 0.0
        avg_margin = sum(margins) / len(margins)
        return max(-0.5, min(0.5, avg_margin))

    def _rapport_signal(self, team) -> float:
        # Confidence in the expert + track record of accuracy.
        trust = (team.average_confidence - 0.5) * 0.6
        expert_trust = (team.expert.appraisal_accuracy - 0.75) * 0.8
        return max(-0.4, min(0.6, trust + expert_trust))

    def _liking_signal(self, team, pick) -> float:
        affinity = team.style_affinity(pick)
        return max(0.0, min(1.0, affinity))

    def _expert_margin_signal(self, pick) -> float:
        est = pick.attributes.get("expert_estimate", pick.shop_price)
        margin = (est - pick.shop_price) / max(1.0, pick.shop_price)
        return max(-0.5, min(0.8, margin))

    def _automate_choice(self, team):
        pick = team.expert_pick_item
        if not pick:
            self.choice_include = False
            self._apply_choice(team)
            return

        perf = self._performance_signal(team)
        rapport = self._rapport_signal(team)
        liking = self._liking_signal(team, pick)
        expert_margin = self._expert_margin_signal(pick)
        noise = (self.episode.rng.random() - 0.5) * 0.1

        score = 0.35 * expert_margin + 0.25 * liking + 0.2 * rapport + 0.15 * perf + noise
        self.auto_score = score
        self.choice_include = score >= 0.05
        self.decision_reason = self._format_reason(perf, rapport, liking, expert_margin)
        self._apply_choice(team)
        self.state = "decision"
        self.phase_timer = 0.0

    def _format_reason(self, perf, rapport, liking, expert_margin) -> str:
        pieces = []
        if perf > 0.1:
            pieces.append("performing well")
        elif perf < -0.1:
            pieces.append("needs a comeback")
        if rapport > 0.1:
            pieces.append("trusts the expert")
        elif rapport < -0.05:
            pieces.append("skeptical of the expert")
        if liking > 0.4:
            pieces.append("likes the style")
        if expert_margin > 0.05:
            pieces.append("sees upside")
        if not pieces:
            return "Gut call after a quick huddle"
        return " & ".join(pieces)

    def _apply_choice(self, team):
        self.episode.mark_expert_choice(team, self.choice_include)

    def _render_choice_buttons(self, surface, x, y):
        include_color = GOOD if self.choice_include else MUTED
        exclude_color = BAD if not self.choice_include else MUTED
        draw_text(surface, "Automated call: include", x, y, self.small, include_color); y += 20
        draw_text(surface, "Automated call: decline", x, y, self.small, exclude_color)

    def render(self, surface):
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))
        draw_text(surface, "Expert Reveal", 24, 18, self.font, TEXT)
        draw_text(surface, "Auto-decide based on performance, rapport, and taste.", 24, 46, self.small, MUTED)

        if not self.active_team:
            draw_text(surface, "All expert picks resolved. Moving to results.", 24, 82, self.small, GOOD)
        else:
            team = self.active_team
            pick = self.active_pick
            draw_text(surface, f"Team: {team.name}  (Expert: {team.expert.name})", 24, 78, self.small, team.color)

            panel_rect = (20, 110, play_w - 40, 200)
            draw_panel(surface, panel_rect)
            draw_text(surface, f"Expert reveals: {pick.name}", 32, 126, self.font, GOLD)
            draw_text(surface, f"Paid: ${pick.shop_price:0.0f}", 32, 158, self.small, TEXT)
            est = pick.attributes.get("expert_estimate", pick.shop_price)
            draw_text(surface, f"Expert thinks it could sell for: ${est:0.0f}", 32, 182, self.small, GOOD if est >= pick.shop_price else BAD)
            draw_text(surface, pick.attributes.get("description", "The team checks if it fits their vibe."), 32, 206, self.micro, MUTED)

            if self.state == "pitch":
                draw_text(surface, "Team inspects the item — waiting for their call...", 32, 236, self.micro, MUTED)
            elif self.state == "decision":
                verdict = "Includes it" if self.choice_include else "Passes on it"
                color = GOOD if self.choice_include else BAD
                draw_text(surface, f"Decision: {verdict} ({self.decision_reason})", 32, 236, self.small, color)
                draw_text(surface, "Host about to reveal the appraiser's view...", 32, 262, self.micro, MUTED)
            elif self.state == "host_reveal":
                appraisal = pick.appraised_value or pick.attributes.get("expert_estimate", pick.shop_price)
                color = GOOD if appraisal >= pick.shop_price else BAD
                verdict = "Included" if self.choice_include else "Declined"
                draw_text(surface, f"Decision: {verdict}", 32, 236, self.small, color)
                draw_text(surface, f"Host reveals appraiser thought: ${appraisal:0.0f}", 32, 262, self.small, color)
                draw_text(surface, "Continuing to the next team...", 32, 286, self.micro, MUTED)

            self._render_choice_buttons(surface, 32, 318)
            draw_text(surface, "Press ENTER to skip ahead", 32, 348, self.micro, MUTED)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "EXPERT_REVEAL",
            time_left=None,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
