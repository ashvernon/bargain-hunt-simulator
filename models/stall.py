from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Stall:
    stall_id: int
    name: str
    rect: tuple[int, int, int, int]  # x,y,w,h
    pricing_style: str               # fair/overpriced/chaotic
    discount_chance: float
    discount_min: float
    discount_max: float
    items: list = field(default_factory=list)

    def center(self):
        x,y,w,h = self.rect
        return (x + w/2, y + h/2)
