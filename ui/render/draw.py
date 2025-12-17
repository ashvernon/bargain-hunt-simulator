import pygame
from constants import TEXT, MUTED, PANEL, PANEL_EDGE

def draw_text(surface, text, x, y, font, color=TEXT):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_panel(surface, rect):
    pygame.draw.rect(surface, PANEL, rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_EDGE, rect, width=2, border_radius=12)
