from __future__ import annotations
from dataclasses import dataclass, field
import math
from models.stall import Stall
from sim.item_factory import make_item
from sim.pricing import set_shop_price

@dataclass
class Market:
    stalls: list[Stall] = field(default_factory=list)
    _next_item_id: int = 1

    @classmethod
    def generate(cls, rng, play_rect):
        x0,y0,w,h = play_rect
        stalls = []
        styles = ["fair", "overpriced", "chaotic"]
        stall_w, stall_h = 170, 110

        # Place stalls in a spaced grid so labels do not overlap while
        # adapting to the available play area width/height.
        total_stalls = 10
        preferred_cols = 4
        min_gap = 24
        cols = preferred_cols if stall_w * preferred_cols + (preferred_cols + 1) * min_gap <= w else 3
        rows = math.ceil(total_stalls / cols)

        gap_x = max(min_gap, (w - cols * stall_w) / (cols + 1))
        gap_y = max(min_gap, (h - rows * stall_h) / (rows + 1))

        layout = []
        for idx in range(total_stalls):
            row = idx // cols
            col = idx % cols
            sx = x0 + gap_x + col * (stall_w + gap_x)
            sy = y0 + gap_y + row * (stall_h + gap_y)
            layout.append((sx, sy))

        for i,(sx,sy) in enumerate(layout, start=1):
            style = rng.choice(styles)
            stall = Stall(
                stall_id=i,
                name=f"Stall {i} ({style})",
                rect=(int(sx), int(sy), stall_w, stall_h),
                pricing_style=style,
                discount_chance=0.18 if style!="overpriced" else 0.10,
                discount_min=0.05,
                discount_max=0.20,
                items=[]
            )
            stalls.append(stall)

        m = cls(stalls=stalls, _next_item_id=1)
        # Populate each stall with items
        for st in m.stalls:
            n = rng.randint(6, 10)
            for _ in range(n):
                it = make_item(rng, m._next_item_id)
                m._next_item_id += 1
                set_shop_price(it, rng, st.pricing_style)
                st.items.append(it)
        return m

    def all_remaining_items(self):
        for st in self.stalls:
            for it in st.items:
                yield it

    def min_item_price(self, default: float = 0.0) -> float:
        prices = [it.shop_price for it in self.all_remaining_items()]
        return min(prices) if prices else default

    def remove_item(self, item):
        for st in self.stalls:
            if item in st.items:
                st.items.remove(item)
                return st
        return None
