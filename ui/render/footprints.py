from __future__ import annotations

from math import sqrt
from typing import Dict, Iterable, Tuple

import pygame

from constants import (
    FOOTPRINT_IMAGE_SIZE,
    FOOTPRINT_LIFETIME,
    FOOTPRINT_STEP_DISTANCE,
    GOLD,
    TEAM_A,
    TEAM_B,
)

Color = Tuple[int, int, int]
Point = Tuple[float, float]


class FootprintSpriteResolver:
    """Provide footprint sprites based on actor roles without relying on binary assets."""

    def __init__(self, footprint_size: tuple[int, int] = FOOTPRINT_IMAGE_SIZE):
        self.footprint_size = footprint_size
        self.sprites: dict[str, pygame.Surface | None] = {
            "red_contestant": self._make_sprite(TEAM_A, badge=False),
            "blue_contestant": self._make_sprite(TEAM_B, badge=False),
            "red_expert": self._make_sprite(TEAM_A, badge=True),
            "blue_expert": self._make_sprite(TEAM_B, badge=True),
            "host": self._make_sprite((164, 132, 84), badge=True, accent=(124, 96, 58)),
        }

    def _team_label(self, color: Color) -> str:
        if color == TEAM_A:
            return "red"
        if color == TEAM_B:
            return "blue"

        def _dist(c1: Iterable[int], c2: Iterable[int]) -> float:
            c1_list, c2_list = list(c1), list(c2)
            return sqrt(sum((c1_list[i] - c2_list[i]) ** 2 for i in range(min(len(c1_list), len(c2_list)))))

        return "red" if _dist(color, TEAM_A) <= _dist(color, TEAM_B) else "blue"

    def _shade(self, color: Color, delta: int) -> Color:
        return tuple(max(0, min(255, c + delta)) for c in color)

    def _make_sprite(self, color: Color, badge: bool, accent: Color | None = None) -> pygame.Surface:
        base = color
        accent = accent or self._shade(color, -32)
        toe = self._shade(color, 24)

        surf = pygame.Surface(self.footprint_size, pygame.SRCALPHA)
        w, h = self.footprint_size

        # left footprint
        pygame.draw.ellipse(surf, base, (w * 0.14, h * 0.18, w * 0.36, h * 0.46))
        pygame.draw.rect(surf, accent, (w * 0.2, h * 0.46, w * 0.22, h * 0.32), border_radius=3)
        pygame.draw.circle(surf, toe, (int(w * 0.28), int(h * 0.18)), int(w * 0.08))

        # right footprint
        pygame.draw.ellipse(surf, toe, (w * 0.48, h * 0.24, w * 0.36, h * 0.46))
        pygame.draw.rect(surf, base, (w * 0.54, h * 0.52, w * 0.22, h * 0.32), border_radius=3)
        pygame.draw.circle(surf, accent, (int(w * 0.62), int(h * 0.22)), int(w * 0.08))

        if badge:
            radius = max(3, min(w, h) // 4)
            pygame.draw.circle(
                surf,
                (*GOLD, 225),
                (w - radius - 2, h - radius - 2),
                radius,
            )

        return surf

    def for_member(self, team, member) -> pygame.Surface | None:
        if getattr(member, "kind", "") == "host":
            return self.sprites.get("host")

        variant = "expert" if getattr(member, "kind", "") == "expert" else "contestant"
        key = f"{self._team_label(getattr(team, 'color', TEAM_A))}_{variant}"
        return self.sprites.get(key)


class FootprintTrailManager:
    """Track recent footprints for actors and render them with fade-out."""

    def __init__(
        self,
        lifetime: float = FOOTPRINT_LIFETIME,
        min_distance: float = FOOTPRINT_STEP_DISTANCE,
    ):
        self.lifetime = lifetime
        self.min_distance = min_distance
        self.footprints: list[dict[str, object]] = []
        self.last_drop: dict[str, Point] = {}
        self.time_elapsed = 0.0

    def update(
        self,
        dt: float,
        actor_positions: Dict[str, Point],
        actor_sprites: Dict[str, pygame.Surface | None],
    ):
        self.time_elapsed += dt
        cutoff = self.time_elapsed - self.lifetime
        self.footprints = [fp for fp in self.footprints if fp["born"] >= cutoff]

        for actor_key, pos in actor_positions.items():
            sprite = actor_sprites.get(actor_key)
            if sprite is None:
                continue

            last_pos = self.last_drop.get(actor_key)
            if last_pos is None:
                self._drop(actor_key, pos, sprite)
                continue

            if self._distance(pos, last_pos) >= self.min_distance:
                self._drop(actor_key, pos, sprite)

    def draw(self, surface: pygame.Surface):
        cutoff = self.time_elapsed - self.lifetime
        for fp in self.footprints:
            born = fp["born"]
            if born < cutoff:
                continue
            age = self.time_elapsed - born
            sprite = fp["sprite"]
            if sprite is None or age < 0:
                continue
            alpha = max(0, min(255, int(255 * (1 - age / self.lifetime))))
            img = sprite if alpha >= 250 else self._with_alpha(sprite, alpha)
            pos = fp["pos"]
            surface.blit(img, (int(pos[0] - img.get_width() / 2), int(pos[1] - img.get_height() / 2)))

    def _drop(self, actor_key: str, pos: Point, sprite: pygame.Surface):
        self.footprints.append({"pos": pos, "born": self.time_elapsed, "sprite": sprite})
        self.last_drop[actor_key] = pos

    def _distance(self, a: Point, b: Point) -> float:
        return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _with_alpha(self, sprite: pygame.Surface, alpha: int) -> pygame.Surface:
        img = sprite.copy()
        img.set_alpha(alpha)
        return img


__all__ = ["FootprintSpriteResolver", "FootprintTrailManager"]
