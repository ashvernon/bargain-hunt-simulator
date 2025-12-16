from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Item:
    item_id: int
    name: str
    category: str
    era: str
    condition: float
    rarity: float
    style_score: float
    true_value: float
    shop_price: float

    appraised_value: float = 0.0
    auction_price: float = 0.0
    is_expert_pick: bool = False
    was_negotiated: bool = False

    @property
    def profit(self) -> float:
        return self.auction_price - self.shop_price
