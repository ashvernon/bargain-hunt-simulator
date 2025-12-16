import pygame
from constants import TEXT, MUTED, GOLD, GOOD, BAD
from ui.render.draw import draw_text, draw_panel

def render_hud(surface, cfg, episode, phase, time_left=None):
    font = pygame.font.SysFont(None, 22)
    small = pygame.font.SysFont(None, 18)
    x0 = cfg.window_w - cfg.hud_w
    panel = (x0 + 10, 10, cfg.hud_w - 20, cfg.window_h - 20)
    draw_panel(surface, panel)

    x = x0 + 24
    y = 26
    draw_text(surface, f"Phase: {phase}", x, y, font); y += 26
    if time_left is not None and phase == "MARKET":
        draw_text(surface, f"Time left: {max(0.0, time_left):0.1f}s", x, y, font, MUTED); y += 26

    y += 8
    for team in episode.teams:
        draw_text(surface, team.name, x, y, font, team.color); y += 20
        draw_text(surface, f"Budget left: ${team.budget_left:0.0f}", x, y, small, MUTED); y += 18

        team_items = [i for i in team.items_bought if not i.is_expert_pick]
        draw_text(surface, f"Items: {len(team_items)}/{cfg.items_per_team}", x, y, small, MUTED); y += 18

        if team.last_action:
            draw_text(surface, team.last_action[:38], x, y, small, TEXT); y += 18

        # show items
        for it in team.items_bought:
            tag = "[EXPERT] " if it.is_expert_pick else ""
            draw_text(surface, f"{tag}{it.name[:26]}", x, y, small, TEXT); y += 16

        y += 10
