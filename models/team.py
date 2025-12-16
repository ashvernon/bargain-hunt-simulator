from __future__ import annotations
from dataclasses import dataclass, field
from models.contestant import Contestant

@dataclass
class Team:
    name: str
    color: tuple[int,int,int]
    budget_start: float
    budget_left: float
    strategy: object
    expert: object
    contestants: list[Contestant]

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

    @property
    def average_confidence(self) -> float:
        if not self.contestants:
            return 0.0
        return sum(c.confidence for c in self.contestants) / len(self.contestants)

    @property
    def average_taste(self) -> float:
        if not self.contestants:
            return 0.0
        return sum(c.taste for c in self.contestants) / len(self.contestants)

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

    def stall_taste_score(self, stall) -> float:
        """How much this duo is drawn to the stall's style and condition."""
        if not stall.items:
            return 0.0
        avg_style = sum(it.style_score for it in stall.items) / len(stall.items)
        avg_condition = sum(it.condition for it in stall.items) / len(stall.items)
        taste = self.average_taste
        return (avg_style * 0.6 + avg_condition * 0.4) * (0.5 + taste)

    def style_affinity(self, item) -> float:
        """Return a multiplier reflecting how much the duo likes this item."""
        return item.style_score * (0.6 + self.average_taste * 0.8)

    def negotiation_bonus(self, expert_bonus: float) -> float:
        """Confidence from both contestants sweetens negotiation odds."""
        return expert_bonus + self.average_confidence * 0.05

    def duo_label(self) -> str:
        names = " & ".join(c.name for c in self.contestants)
        return f"{self.name}: {names}"

    def role_blurb(self) -> str:
        return ", ".join(f"{c.name} ({c.role})" for c in self.contestants)
