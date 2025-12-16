from __future__ import annotations
from dataclasses import dataclass, field
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
        # Place 6 stalls around the map
        layout = [
            (x0+60,  y0+60),
            (x0+w-220, y0+70),
            (x0+80,  y0+h-180),
            (x0+w-240, y0+h-190),
            (x0+w/2-80, y0+120),
            (x0+w/2-80, y0+h-230),
        ]
        for i,(sx,sy) in enumerate(layout, start=1):
            style = rng.choice(styles)
            stall = Stall(
                stall_id=i,
                name=f"Stall {i} ({style})",
                rect=(int(sx), int(sy), 170, 110),
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

    def remove_item(self, item):
        for st in self.stalls:
            if item in st.items:
                st.items.remove(item)
                return st
        return None
