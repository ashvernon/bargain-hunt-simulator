import pygame
from constants import TEXT, MUTED, GOLD, GOOD, BAD
from ui.render.draw import draw_text, draw_panel


def _format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes, secs = divmod(int(seconds), 60)
    if minutes:
        return f"{minutes:d}:{secs:02d}"
    return f"{secs:d}s"

def render_hud(surface, cfg, episode, phase, time_left=None, speed: float = 1.0):
    font = pygame.font.SysFont(None, 22)
    small = pygame.font.SysFont(None, 18)
    x0 = cfg.window_w - cfg.hud_w
    panel = (x0 + 10, 10, cfg.hud_w - 20, cfg.window_h - 20)
    draw_panel(surface, panel)

    x = x0 + 24
    y = 26
    draw_text(surface, f"Phase: {phase}", x, y, font); y += 26
    if time_left is not None and phase == "MARKET":
        draw_text(surface, f"Time left: {_format_time(time_left)}", x, y, font, MUTED); y += 26
    draw_text(surface, f"Speed: {speed:.1f}x (press F)", x, y, small, MUTED); y += 22

    y += 8
    for team in episode.teams:
        draw_text(surface, team.name, x, y, font, team.color); y += 20
        draw_text(surface, team.role_blurb(), x, y, small, team.color); y += 18
        draw_text(surface, f"Confidence: {team.average_confidence:.2f}  Taste: {team.average_taste:.2f}", x, y, small, MUTED); y += 18
        draw_text(surface, f"Budget left: ${team.budget_left:0.0f}", x, y, small, MUTED); y += 18

        if getattr(team, "expert_pick_budget", 0) > 0:
            draw_text(surface, f"Expert budget ready: ${team.expert_pick_budget:0.0f}", x, y, small, GOLD); y += 18

        team_items = team.team_items
        draw_text(surface, f"Items: {len(team_items)}/{cfg.items_per_team}", x, y, small, MUTED); y += 18

        if team.last_action:
            draw_text(surface, team.last_action[:38], x, y, small, TEXT); y += 18

        # show items
        for it in team_items:
            draw_text(surface, f"{it.name[:26]}", x, y, small, TEXT); y += 16

        if getattr(team, "expert_pick_item", None):
            status = team.expert_pick_included
            if status is None:
                draw_text(surface, "Expert pick: hidden until reveal", x, y, small, GOLD); y += 16
            elif status:
                draw_text(surface, f"[EXPERT] {team.expert_pick_item.name[:24]}", x, y, small, TEXT); y += 16
            else:
                draw_text(surface, "Expert pick declined", x, y, small, MUTED); y += 16
        elif getattr(team, "expert_pick_budget", 0) >= 1.0:
            draw_text(surface, "Expert is shopping soon...", x, y, small, MUTED); y += 16

        y += 10
