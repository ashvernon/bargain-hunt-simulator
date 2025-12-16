from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    color: tuple[int,int,int]
    budget_start: float
    budget_left: float
    strategy: object
    expert: object

    # Movement
    x: float
    y: float
    target_stall_id: int | None = None

    # Purchases and outcomes
    items_bought: list = field(default_factory=list)
    spend: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    golden_gavel: bool = False

    last_action: str = ""

    def pos(self):
        return (self.x, self.y)

    def can_buy_more(self, items_per_team: int) -> bool:
        # only counts team-bought items
        team_items = [i for i in self.items_bought if not i.is_expert_pick]
        return len(team_items) < items_per_team

    def distance_to(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return (dx*dx + dy*dy) ** 0.5
