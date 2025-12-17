import math
import random
import pygame

from constants import (
    STALL,
    STALL_EDGE,
    STALL_GRAD_BOTTOM,
    STALL_GRAD_TOP,
    STALL_LIP,
    STALL_LIP_EDGE,
    STALL_SILHOUETTE,
    STALL_ACTIVE_EDGE,
    STALL_ACTIVE_GLOW,
    STALL_TYPE_TINT_FAIR,
    STALL_TYPE_TINT_OVERPRICED,
    STALL_TYPE_TINT_CHAOTIC,
    STALL_TYPE_LABEL_FAIR,
    STALL_TYPE_LABEL_OVERPRICED,
    STALL_TYPE_LABEL_CHAOTIC,
    TEXT,
    MUTED,
)


class StallCardRenderer:
    def __init__(self):
        self._surface_cache: dict[tuple[int, str, int, int], tuple[pygame.Surface, float]] = {}
        self._highlight_cache: dict[tuple[int, int, float], pygame.Surface] = {}
        self._silhouettes = self._build_silhouettes()
        self._type_tints = {
            "fair": STALL_TYPE_TINT_FAIR,
            "overpriced": STALL_TYPE_TINT_OVERPRICED,
            "chaotic": STALL_TYPE_TINT_CHAOTIC,
        }
        self._type_labels = {
            "fair": STALL_TYPE_LABEL_FAIR,
            "overpriced": STALL_TYPE_LABEL_OVERPRICED,
            "chaotic": STALL_TYPE_LABEL_CHAOTIC,
        }
        self._type_icons = {
            "fair": "🫖",
            "overpriced": "💰",
            "chaotic": "🎲",
        }

    def draw(self, surface, stall, title_font, meta_font, *, is_active: bool = False):
        x, y, w, h = stall.rect
        card_surface, rotation = self._get_surface(stall)
        card_rect = card_surface.get_rect(center=(x + w / 2, y + h / 2))
        surface.blit(card_surface, card_rect)

        if is_active:
            highlight = self._get_highlight_surface(w, h, rotation)
            pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() / 1000.0 * 2.2)
            highlight.set_alpha(int(80 + 70 * pulse))
            highlight_rect = highlight.get_rect(center=card_rect.center)
            surface.blit(highlight, highlight_rect)

        anchor_x = card_rect.centerx - w / 2
        anchor_y = card_rect.centery - h / 2

        draw_x = anchor_x + 12
        draw_y = anchor_y + 12
        title_color = TEXT
        meta_color = MUTED

        title_surface = title_font.render(stall.name, True, title_color)
        surface.blit(title_surface, (draw_x, draw_y))

        pricing_style = (stall.pricing_style or "").lower()
        type_label = pricing_style.capitalize() if pricing_style else ""
        label_color = self._type_labels.get(pricing_style, meta_color)
        if type_label:
            label_surface = meta_font.render(type_label, True, label_color)
            surface.blit(label_surface, (draw_x, draw_y + 20))

        icon = self._type_icons.get(pricing_style, "📦")
        item_text = f"{icon} ×{len(stall.items)}"
        item_surface = meta_font.render(item_text, True, title_color)
        surface.blit(item_surface, (draw_x, draw_y + 40))

    def _get_surface(self, stall):
        x, y, w, h = stall.rect
        key = (stall.stall_id, stall.pricing_style, w, h)
        if key in self._surface_cache:
            return self._surface_cache[key]

        rotation = self._rotation_for_style(stall.pricing_style, stall.stall_id)
        base_surface = self._build_base_surface(w, h, stall)
        if rotation:
            base_surface = pygame.transform.rotate(base_surface, rotation)

        self._surface_cache[key] = (base_surface, rotation)
        return self._surface_cache[key]

    def _build_base_surface(self, w: int, h: int, stall):
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        style = (stall.pricing_style or "").lower()
        tint = self._type_tints.get(style, (0, 0, 0))

        for row in range(h):
            mix = row / max(1, h - 1)
            r = self._lerp(STALL_GRAD_TOP[0], STALL_GRAD_BOTTOM[0], mix)
            g = self._lerp(STALL_GRAD_TOP[1], STALL_GRAD_BOTTOM[1], mix)
            b = self._lerp(STALL_GRAD_TOP[2], STALL_GRAD_BOTTOM[2], mix)
            tinted = self._apply_tint((r, g, b), tint, 0.65)
            surface.fill(tinted, rect=pygame.Rect(0, row, w, 1))

        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), (0, 0, w, h), border_radius=10)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.fill((*STALL, 28), special_flags=pygame.BLEND_RGBA_ADD)

        lip_height = max(10, int(h * 0.12))
        lip_rect = pygame.Rect(6, h - lip_height - 4, w - 12, lip_height)
        pygame.draw.rect(surface, STALL_LIP, lip_rect, border_radius=6)
        pygame.draw.rect(surface, STALL_LIP_EDGE, lip_rect.inflate(-4, -4), border_radius=4)

        silhouette_rng = random.Random(stall.stall_id * 9973)
        silhouettes = silhouette_rng.sample(self._silhouettes, k=min(2, len(self._silhouettes)))
        for idx, sil in enumerate(silhouettes):
            scale = silhouette_rng.uniform(0.7, 1.15)
            sil_w = int(sil.get_width() * scale)
            sil_h = int(sil.get_height() * scale)
            sil_surface = pygame.transform.smoothscale(sil, (sil_w, sil_h))
            pad_x = 18 + idx * 14
            pad_y = 18 + idx * 10
            pos_x = pad_x + silhouette_rng.randint(0, max(4, w - sil_w - pad_x * 2))
            pos_y = pad_y + silhouette_rng.randint(0, max(6, h - sil_h - pad_y * 2))
            surface.blit(sil_surface, (pos_x, pos_y))

        if style == "chaotic":
            self._add_contrast_strokes(surface, stall.stall_id)

        pygame.draw.rect(surface, STALL_EDGE, (0, 0, w, h), width=2, border_radius=10)
        inner_rect = pygame.Rect(4, 4, w - 8, h - 8)
        pygame.draw.rect(surface, STALL_EDGE, inner_rect, width=1, border_radius=8)
        return surface.convert_alpha()

    def _rotation_for_style(self, style: str, stall_id: int) -> float:
        if (style or "").lower() != "chaotic":
            return 0.0
        rnd = random.Random(stall_id * 313)
        return rnd.uniform(-2.0, 2.0)

    def _add_contrast_strokes(self, surface: pygame.Surface, stall_id: int):
        rnd = random.Random(stall_id * 197)
        w, h = surface.get_size()
        for _ in range(10):
            sw = rnd.randint(18, 34)
            sh = rnd.randint(4, 10)
            x = rnd.randint(8, max(8, w - sw - 8))
            y = rnd.randint(8, max(8, h - sh - 8))
            alpha = rnd.randint(20, 40)
            stroke = pygame.Surface((sw, sh), pygame.SRCALPHA)
            stroke.fill((*STALL_EDGE, alpha))
            surface.blit(stroke, (x, y), special_flags=pygame.BLEND_PREMULTIPLIED)

    def _get_highlight_surface(self, w: int, h: int, rotation: float):
        key = (w, h, rotation)
        if key not in self._highlight_cache:
            glow_surface = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
            glow_rect = glow_surface.get_rect().inflate(-4, -4)
            pygame.draw.rect(glow_surface, (*STALL_ACTIVE_GLOW, 18), glow_rect, border_radius=12)
            pygame.draw.rect(glow_surface, (*STALL_ACTIVE_EDGE, 90), glow_rect, width=2, border_radius=12)
            pygame.draw.rect(glow_surface, (*STALL_ACTIVE_EDGE, 120), glow_rect.inflate(-6, -6), width=1, border_radius=10)
            if rotation:
                glow_surface = pygame.transform.rotate(glow_surface, rotation)
            self._highlight_cache[key] = glow_surface
        return self._highlight_cache[key].copy()

    def _build_silhouettes(self):
        return [
            self._build_teacup(),
            self._build_clock(),
            self._build_vase(),
            self._build_frame(),
        ]

    def _build_teacup(self):
        surf = pygame.Surface((44, 34), pygame.SRCALPHA)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (6, 12, 26, 14), border_radius=6)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (12, 8, 22, 8), border_radius=4)
        pygame.draw.circle(surf, STALL_SILHOUETTE, (32, 19), 6)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (10, 24, 22, 4))
        return surf.convert_alpha()

    def _build_clock(self):
        surf = pygame.Surface((38, 38), pygame.SRCALPHA)
        pygame.draw.circle(surf, STALL_SILHOUETTE, (19, 19), 16)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (16, 2, 6, 6), border_radius=2)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (16, 30, 6, 6), border_radius=2)
        pygame.draw.line(surf, STALL_SILHOUETTE, (19, 19), (19, 9), 3)
        pygame.draw.line(surf, STALL_SILHOUETTE, (19, 19), (27, 22), 3)
        return surf.convert_alpha()

    def _build_vase(self):
        surf = pygame.Surface((40, 44), pygame.SRCALPHA)
        polygon = [(14, 4), (26, 4), (30, 14), (26, 30), (28, 40), (12, 40), (14, 30), (10, 14)]
        pygame.draw.polygon(surf, STALL_SILHOUETTE, polygon)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (16, 2, 8, 4), border_radius=2)
        return surf.convert_alpha()

    def _build_frame(self):
        surf = pygame.Surface((50, 36), pygame.SRCALPHA)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (4, 4, 42, 28), border_radius=4)
        pygame.draw.rect(surf, (*STALL_SILHOUETTE[:3], 0), (10, 10, 30, 16), border_radius=3)
        pygame.draw.rect(surf, STALL_SILHOUETTE, (14, 12, 10, 2))
        pygame.draw.rect(surf, STALL_SILHOUETTE, (28, 18, 12, 2))
        return surf.convert_alpha()

    def _apply_tint(self, base_color: tuple[int, int, int], tint: tuple[int, int, int], strength: float):
        return tuple(
            max(0, min(255, int(c + t * strength))) for c, t in zip(base_color, tint)
        )

    def _lerp(self, a: float, b: float, t: float) -> int:
        return int(a + (b - a) * t)
