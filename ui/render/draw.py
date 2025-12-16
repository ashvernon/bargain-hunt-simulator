import pygame
from constants import TEXT, MUTED, PANEL

def draw_text(surface, text, x, y, font, color=TEXT):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_panel(surface, rect):
    pygame.draw.rect(surface, PANEL, rect, border_radius=10)
