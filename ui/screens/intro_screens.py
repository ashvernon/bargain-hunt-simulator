import pygame
from ui.screens.screen_base import Screen
from ui.render.draw import draw_panel, draw_text
from constants import BG, TEXT, MUTED, ACCENT, GOLD, CANVAS, PANEL_EDGE, PANEL


def _render_intro_panel(surface, cfg, title, subtitle, footer=True):
    surface.fill(BG)
    padding = cfg.margin * 2
    panel_rect = (padding, padding, cfg.window_w - padding * 2, cfg.window_h - padding * 2)
    draw_panel(surface, panel_rect)

    title_font = pygame.font.SysFont(None, 44)
    subtitle_font = pygame.font.SysFont(None, 26)
    footer_font = pygame.font.SysFont(None, 18)
    x = panel_rect[0] + cfg.margin
    y = panel_rect[1] + cfg.margin

    draw_text(surface, title, x, y, title_font, TEXT)
    y += 48
    if subtitle:
        draw_text(surface, subtitle, x, y, subtitle_font, MUTED)
        y += 36

    if footer:
        footer_text = "Press Enter to continue • Space to skip intro"
        draw_text(surface, footer_text, x, panel_rect[1] + panel_rect[3] - cfg.margin - 20, footer_font, MUTED)

    return x, y


class HostWelcomeScreen(Screen):
    def __init__(self, cfg):
        self.cfg = cfg
        self.body_font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 20)

    def render(self, surface):
        x, y = _render_intro_panel(surface, self.cfg, "Welcome to Bargain Hunt!", "Your host is ready to kick things off.")
        draw_text(surface, "Good evening treasure hunters! I'm your host, and today our teams", x, y, self.body_font, TEXT); y += 30
        draw_text(surface, "will scour the market for deals, haggle with stall owners, and hope", x, y, self.body_font, TEXT); y += 30
        draw_text(surface, "their finds shine at auction. Let's meet the contestants!", x, y, self.body_font, TEXT); y += 36
        draw_text(surface, "You can skip this intro any time with Space.", x, y, self.small, MUTED)


class ContestantIntroScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.title_font = pygame.font.SysFont(None, 28)
        self.body_font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)

    def render(self, surface):
        x, y = _render_intro_panel(surface, self.cfg, "Meet the teams", "Contestants and starting budgets")
        col_width = (self.cfg.window_w - self.cfg.margin * 4) // 2
        for idx, team in enumerate(self.episode.teams):
            cx = x + idx * col_width
            ty = y
            draw_text(surface, team.name, cx, ty, self.title_font, team.color); ty += 28
            draw_text(surface, team.role_blurb(), cx, ty, self.body_font, TEXT); ty += 24
            draw_text(surface, f"Average confidence: {team.average_confidence:.2f}", cx, ty, self.small, MUTED); ty += 20
            draw_text(surface, f"Average taste: {team.average_taste:.2f}", cx, ty, self.small, MUTED); ty += 20
            draw_text(surface, f"Starting budget: ${team.budget_start:.0f}", cx, ty, self.body_font, ACCENT); ty += 28
            draw_text(surface, f"Shopping list: {self.episode.items_per_team} items", cx, ty, self.small, MUTED)


class ExpertAssignmentScreen(Screen):
    def __init__(self, cfg, episode):
        self.cfg = cfg
        self.episode = episode
        self.title_font = pygame.font.SysFont(None, 28)
        self.body_font = pygame.font.SysFont(None, 22)
        self.small = pygame.font.SysFont(None, 18)
        self.stat_font = pygame.font.SysFont(None, 20)
        self.badge_font = pygame.font.SysFont(None, 16)

    def render(self, surface):
        x, y = _render_intro_panel(surface, self.cfg, "Expert assignments", "Each team is paired with a specialist for the hunt.")
        cards_per_row = 2 if len(self.episode.teams) > 1 else 1
        gutter = self.cfg.margin
        content_width = self.cfg.window_w - self.cfg.margin * 6
        card_width = (content_width - gutter * (cards_per_row - 1)) // cards_per_row
        card_height = 170
        card_padding = self.cfg.margin

        for idx, team in enumerate(self.episode.teams):
            row = idx // cards_per_row
            col = idx % cards_per_row
            card_x = x + col * (card_width + gutter)
            card_y = y + row * (card_height + gutter)

            pygame.draw.rect(surface, CANVAS, (card_x, card_y, card_width, card_height), border_radius=10)
            pygame.draw.rect(surface, PANEL_EDGE, (card_x, card_y, card_width, card_height), width=2, border_radius=10)
            pygame.draw.rect(surface, team.color, (card_x, card_y, card_width, 8), border_radius=10)

            inner_x = card_x + card_padding
            inner_y = card_y + card_padding
            draw_text(surface, f"{team.name}", inner_x, inner_y, self.title_font, team.color)

            portrait_size = 70
            portrait_rect = pygame.Rect(inner_x, inner_y + 18, portrait_size, portrait_size)
            pygame.draw.rect(surface, PANEL, portrait_rect, border_radius=8)
            pygame.draw.rect(surface, PANEL_EDGE, portrait_rect, width=2, border_radius=8)
            placeholder_label = "Image"
            label_img = self.badge_font.render(placeholder_label, True, MUTED)
            label_pos = (
                portrait_rect.x + (portrait_size - label_img.get_width()) // 2,
                portrait_rect.y + (portrait_size - label_img.get_height()) // 2,
            )
            surface.blit(label_img, label_pos)

            info_x = portrait_rect.right + card_padding
            info_y = inner_y + 14
            draw_text(surface, f"Expert: {team.expert.name}", info_x, info_y, self.body_font, GOLD); info_y += 26
            draw_text(surface, f"Negotiation boost: {team.expert.negotiation_bonus*100:.0f}%", info_x, info_y, self.stat_font, ACCENT); info_y += 22
            fav = ", ".join(team.expert.bias.keys()) if getattr(team.expert, "bias", None) else "All categories"
            draw_text(surface, f"Specialty: {fav}", info_x, info_y, self.stat_font, MUTED)

            flavor_y = portrait_rect.bottom + card_padding // 2
            draw_text(surface, "Lean on your expert for", inner_x, flavor_y, self.small, TEXT); flavor_y += 18
            draw_text(surface, "valuations and deal-making.", inner_x, flavor_y, self.small, TEXT)

        rows = (len(self.episode.teams) + cards_per_row - 1) // cards_per_row
        y += rows * (card_height + gutter) + gutter
        draw_text(surface, "Each expert is ready with tips and quick appraisals.", x, y, self.body_font, TEXT)


class MarketSendoffScreen(Screen):
    def __init__(self, cfg):
        self.cfg = cfg
        self.body_font = pygame.font.SysFont(None, 26)
        self.small = pygame.font.SysFont(None, 20)

    def render(self, surface):
        x, y = _render_intro_panel(surface, self.cfg, "Ready, set, bargain!", "The hunt begins at the market.")
        draw_text(surface, "Teams, you have one hour to uncover the best bargains you can.", x, y, self.body_font, TEXT); y += 30
        draw_text(surface, "Work fast, trust your instincts, and keep an eye on that budget.", x, y, self.body_font, TEXT); y += 30
        draw_text(surface, "Head to the market floor when you're ready.", x, y, self.body_font, ACCENT); y += 34
        draw_text(surface, "Press Enter to start the market now, or Space to skip intros anytime.", x, y, self.small, MUTED)
