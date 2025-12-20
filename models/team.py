from __future__ import annotations
from dataclasses import dataclass, field
from models.contestant import Contestant, RelationshipType
from typing import List

@dataclass
class TeamMemberState:
    key: str
    label: str
    role: str
    kind: str  # contestant | expert

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
    member_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    member_roles: dict[str, str] = field(default_factory=dict)
    heading: tuple[float, float] = (1.0, 0.0)

    relationship: str | None = None
    relationship_type: RelationshipType | None = None
    target_stall_id: int | None = None

    # Purchases and outcomes
    items_bought: list = field(default_factory=list)
    expert_pick_budget: float = 0.0
    expert_pick_item: object | None = None
    expert_pick_included: bool | None = None
    spend: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    golden_gavel: bool = False

    last_action: str = ""
    spend_plan = None
    stall_cooldowns: dict[int, float] = field(default_factory=dict)
    market_state: str = "BROWSING"
    state_timer: float = 0.0
    decision_context: dict | None = None
    considered_items: list[dict] = field(default_factory=list)
    time_spent_considering: float = 0.0
    time_spent_consulting: float = 0.0
    revisit_probability: float = 0.0

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
        return len(self.team_items) < items_per_team

    def distance_to(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return (dx*dx + dy*dy) ** 0.5

    @property
    def team_items(self):
        return [i for i in self.items_bought if not i.is_expert_pick]

    @property
    def team_item_count(self) -> int:
        return len(self.team_items)

    @property
    def included_items(self) -> List:
        items = list(self.items_bought)
        if self.expert_pick_included and self.expert_pick_item:
            if self.expert_pick_item not in items:
                items.append(self.expert_pick_item)
        return items

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

    @property
    def members(self) -> list[TeamMemberState]:
        roster = [
            TeamMemberState(
                key=f"contestant_{idx}",
                label=c.name,
                role=c.role,
                kind="contestant",
            )
            for idx, c in enumerate(self.contestants)
        ]
        if self.expert:
            roster.append(
                TeamMemberState(
                    key="expert",
                    label=getattr(self.expert, "name", "Expert"),
                    role=getattr(self.expert, "signature_style", "Expert"),
                    kind="expert",
                )
            )
        return roster

    def ensure_member_positions(self):
        origin = self.pos()
        for member in self.members:
            self.member_positions.setdefault(member.key, origin)
            if member.role and member.key not in self.member_roles:
                self.member_roles[member.key] = member.role

    def member_pos(self, member_key: str) -> tuple[float, float]:
        return self.member_positions.get(member_key, self.pos())
