from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from models.item import Item
from models.team import Team


@dataclass
class AuctionLotResult:
    item_id: int
    name: str
    category: str
    paid: float
    appraised: float
    sold: float
    profit: float
    image_path: str | None
    is_expert_pick: bool = False


@dataclass
class AuctionRoundResult:
    team_name: str
    team_color: tuple[int, int, int]
    lots: list[AuctionLotResult]
    spent_total: float
    sold_total: float
    profit_total: float
    roi: float
    sold_count: int
    total_count: int
    best_lot: AuctionLotResult | None
    worst_lot: AuctionLotResult | None

    @classmethod
    def from_team(cls, team: Team, items: Iterable[Item]) -> "AuctionRoundResult":
        lots = [
            AuctionLotResult(
                item_id=item.item_id,
                name=item.name,
                category=item.category,
                paid=item.shop_price,
                appraised=item.appraised_value,
                sold=item.auction_price,
                profit=item.auction_price - item.shop_price,
                image_path=item.image_path,
                is_expert_pick=item.is_expert_pick,
            )
            for item in items
        ]

        spent_total = sum(lot.paid for lot in lots)
        sold_total = sum(lot.sold for lot in lots)
        profit_total = sold_total - spent_total
        roi = (sold_total / spent_total - 1) if spent_total else 0.0
        best_lot = max(lots, key=lambda l: l.profit, default=None)
        worst_lot = min(lots, key=lambda l: l.profit, default=None)

        return cls(
            team_name=team.name,
            team_color=team.color,
            lots=lots,
            spent_total=spent_total,
            sold_total=sold_total,
            profit_total=profit_total,
            roi=roi,
            sold_count=len(lots),
            total_count=len(lots),
            best_lot=best_lot,
            worst_lot=worst_lot,
        )
