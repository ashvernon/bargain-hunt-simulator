import pygame
from ui.screens.screen_base import Screen
from ui.render.hud import render_hud
from ui.render.draw import draw_text
from ui.render.stall_card import StallCardRenderer
from constants import (
    BG,
    GOOD,
    HOST_ACCENT,
    HOST_OUTLINE,
    HOST_RADIUS,
    TEAM_EXPERT_ACCENT,
    TEAM_EXPERT_RADIUS,
    TEAM_MARKER_OUTLINE,
    TEAM_MEMBER_RADIUS,
)

class MarketScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.time_left = None
        self.font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)
        self.stall_renderer = StallCardRenderer()

    def set_time_left(self, t):
        self.time_left = t

    def _draw_team_members(self, surface, team):
        for member in team.members:
            px, py = team.member_pos(member.key)
            pos = (int(px), int(py))
            is_expert = member.kind == "expert"
            radius = TEAM_EXPERT_RADIUS if is_expert else TEAM_MEMBER_RADIUS
            fill = TEAM_EXPERT_ACCENT if is_expert else team.color

            pygame.draw.circle(surface, TEAM_MARKER_OUTLINE, pos, radius + 2)
            pygame.draw.circle(surface, fill, pos, radius)

    def _draw_host(self, surface):
        host = getattr(self.episode, "host", None)
        if not host or host.state == "GONE":
            return

        pos = (int(host.x), int(host.y))
        pygame.draw.circle(surface, HOST_OUTLINE, pos, HOST_RADIUS + 3)
        pygame.draw.circle(surface, HOST_ACCENT, pos, HOST_RADIUS)
        step_offset = HOST_RADIUS // 2
        footprint_points = [
            (pos[0] - step_offset, pos[1] + HOST_RADIUS + 2),
            (pos[0] + step_offset, pos[1] + HOST_RADIUS + 2),
            (pos[0], pos[1] + HOST_RADIUS + 4),
        ]
        pygame.draw.polygon(surface, HOST_OUTLINE, footprint_points)

    def render(self, surface):
        # play area
        play_w = self.cfg.window_w - self.cfg.hud_w
        pygame.draw.rect(surface, BG, (0, 0, play_w, self.cfg.window_h))

        active_stalls = set()
        for team in self.episode.teams:
            if team.target_stall_id is not None:
                active_stalls.add(team.target_stall_id)
            ctx = team.decision_context or {}
            if ctx.get("stall_id") is not None:
                active_stalls.add(ctx.get("stall_id"))

        for st in self.episode.market.stalls:
            self.stall_renderer.draw(
                surface,
                st,
                self.small,
                self.small,
                is_active=st.stall_id in active_stalls,
            )

        self._draw_host(surface)

        # teams
        for team in self.episode.teams:
            self._draw_team_members(surface, team)
            draw_text(surface, team.duo_label(), int(team.x)+12, int(team.y)-10, self.small, team.color)
            if len(team.team_items) >= self.cfg.items_per_team:
                draw_text(surface, "Done shopping", int(team.x)+12, int(team.y)+8, self.small, GOOD)

        render_hud(
            surface,
            self.cfg,
            self.episode,
            "MARKET",
            time_left=self.time_left,
            speed=getattr(self.episode, "time_scale", 1.0),
        )
