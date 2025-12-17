from __future__ import annotations
from dataclasses import dataclass
from constants import TEAM_A, TEAM_B
from sim.rng import RNG
from models.market import Market
from models.team import Team
from models.item import Item
from models.expert import Expert
from models.auctioneer import Auctioneer
from models.auction_house import AuctionHouse
from sim.pricing import negotiate
from sim.scoring import compute_team_totals, golden_gavel
from ai.strategy_value import ValueHunterStrategy
from ai.strategy_risk import RiskAverseStrategy
from sim.team_generator import generate_random_teams

@dataclass
class AuctionLot:
    team: Team
    item: Item
    position_in_team: int
    team_total: int
    is_bonus: bool

@dataclass
class Episode:
    ep_idx: int
    seed: int
    play_rect: tuple[int,int,int,int]
    items_per_team: int
    starting_budget: float
    expert_min_budget: float = 1.0
    time_scale: float = 1.0

    def setup(self):
        self.rng = RNG(self.seed)
        self.market = Market.generate(self.rng, self.play_rect)
        self.auction_house = AuctionHouse.generate(self.rng)
        self.auctioneer = Auctioneer("Chloe", accuracy=0.83, bias={"silverware": 1.05})

        # Experts
        exp_a = Expert("Natasha", accuracy=0.80, negotiation_bonus=0.08, bias={"glassware": 1.06})
        exp_b = Expert("Raj", accuracy=0.76, negotiation_bonus=0.06, bias={"tools": 1.08})

        # Teams
        x0,y0,w,h = self.play_rect
        team_profiles = generate_random_teams(self.rng, color_labels=["Red", "Blue"])
        team_slots = [
            {
                "profile": team_profiles[0],
                "color": TEAM_A,
                "strategy": ValueHunterStrategy(),
                "expert": exp_a,
                "pos": (x0 + 90, y0 + h / 2),
            },
            {
                "profile": team_profiles[1],
                "color": TEAM_B,
                "strategy": RiskAverseStrategy(),
                "expert": exp_b,
                "pos": (x0 + w - 120, y0 + h / 2),
            },
        ]

        self.teams = [
            Team(
                slot["profile"].name,
                slot["color"],
                self.starting_budget,
                self.starting_budget,
                slot["strategy"],
                slot["expert"],
                slot["profile"].contestants,
                slot["pos"][0],
                slot["pos"][1],
                relationship=slot["profile"].relationship,
                relationship_type=slot["profile"].relationship_type,
            )
            for slot in team_slots
        ]

        for team in self.teams:
            team.spend_plan = team.strategy.choose_spend_plan(self.rng)

        self.appraisal_done = False
        self.auction_done = False
        self.results_done = False
        self.auction_queue = []  # list of AuctionLot
        self.auction_cursor = 0
        self.auction_stage = "team"
        self.auction_label = "Team items first"
        self.last_sold = None

    def update_market_ai(self, dt: float, team_speed: float, buy_radius: float):
        # Simple AI: pick a target stall; move; when close, attempt to buy.
        for team in self.teams:
            # decay stall cooldowns
            for sid in list(team.stall_cooldowns.keys()):
                remaining = team.stall_cooldowns[sid] - dt
                if remaining <= 0:
                    del team.stall_cooldowns[sid]
                else:
                    team.stall_cooldowns[sid] = remaining

            if not team.spend_plan:
                team.spend_plan = team.strategy.choose_spend_plan(self.rng)

            if not team.can_buy_more(self.items_per_team):
                team.last_action = "Done shopping"
                continue

            # choose target stall if none / empty
            target = None
            if team.target_stall_id is not None:
                target = next((s for s in self.market.stalls if s.stall_id == team.target_stall_id), None)
                if target and not target.items:
                    target = None

            if target and not self._stall_has_affordable_item(team, target):
                team.stall_cooldowns[target.stall_id] = 3.0
                target = None

            forced_choice = False
            if target is None:
                target = team.strategy.pick_target_stall(self.market, team, self.rng, self.items_per_team)
                team.target_stall_id = target.stall_id if target else None

            if target is None:
                target = self._pick_desperation_stall(team)
                forced_choice = target is not None
                team.target_stall_id = target.stall_id if target else None

            if not target:
                team.last_action = "No stalls left"
                continue

            tx, ty = target.center()
            # move
            self._move_towards(team, tx, ty, dt, team_speed)

            # purchase if close enough
            if team.distance_to(tx, ty) <= buy_radius:
                item = team.strategy.decide_purchase(self.market, team, target, self.rng, self.items_per_team)
                if not item and forced_choice:
                    item = self._pick_cheapest_affordable_item(target, team)

                if item:
                    self._complete_purchase(team, target, item)
                else:
                    team.stall_cooldowns[target.stall_id] = 3.0
                    team.target_stall_id = None
                    team.last_action = "Expert says: keep looking"

    def _reserved_expert_budget(self, team) -> float:
        """Minimum cash that must be held back for the expert pick."""
        return self.expert_min_budget if team.team_item_count < self.items_per_team else 0.0

    def _usable_budget(self, team) -> float:
        return max(0.0, team.budget_left - self._reserved_expert_budget(team))

    def _stall_has_affordable_item(self, team, stall) -> bool:
        usable_budget = self._usable_budget(team)
        if usable_budget <= 0:
            return False

        min_expected_price = min(12.0, self.market.min_item_price(default=12.0))
        remaining_slots = self.items_per_team - team.team_item_count
        for it in stall.items:
            if it.shop_price > usable_budget:
                continue
            if team.spend_plan and team.spend_plan.allows_purchase(
                price=it.shop_price,
                purchase_index=team.team_item_count,
                budget_start=team.budget_start,
                budget_left=usable_budget,
                remaining_slots=remaining_slots,
                min_expected_price=min_expected_price,
            ):
                return True
            if not team.spend_plan:
                return True
        return False

    def _pick_desperation_stall(self, team):
        """Pick a stall when strategies deem everything unsuitable.

        This keeps teams moving instead of getting stuck on "No stalls left".
        We ignore spend plans and choose the cheapest stall that still has an
        item the team can afford.
        """
        candidates = [
            st
            for st in self.market.stalls
            if st.items and team.stall_cooldowns.get(st.stall_id, 0) <= 0
        ]
        if not candidates:
            return None

        usable_budget = self._usable_budget(team)
        best = None
        best_price = float("inf")
        for st in candidates:
            cheapest = min((it.shop_price for it in st.items if it.shop_price <= usable_budget), default=None)
            if cheapest is not None and cheapest < best_price:
                best_price, best = cheapest, st
        return best

    def _pick_cheapest_affordable_item(self, stall, team):
        if not stall or not stall.items:
            return None
        usable_budget = self._usable_budget(team)
        affordable = [it for it in stall.items if it.shop_price <= usable_budget]
        if not affordable:
            return None
        return min(affordable, key=lambda it: it.shop_price)

    def _complete_purchase(self, team, target, item):
        # negotiate (expert helps)
        neg_bonus = team.negotiation_bonus(team.expert.negotiation_bonus)
        did, disc = negotiate(
            item,
            self.rng,
            target.discount_chance,
            target.discount_min,
            target.discount_max,
            expert_bonus=neg_bonus,
        )
        item.was_negotiated = did
        reserve_needed = self.expert_min_budget if team.team_item_count < self.items_per_team else 0.0
        if item.shop_price > team.budget_left:
            team.last_action = "Couldn't afford after negotiation"
            return
        remaining_after_buy = round(team.budget_left - item.shop_price, 2)
        if remaining_after_buy < reserve_needed:
            team.last_action = f"Need ${reserve_needed:0.0f} saved for expert"
            team.stall_cooldowns[target.stall_id] = 2.5
            team.target_stall_id = None
            return
        target.items.remove(item)
        team.items_bought.append(item)
        team.budget_left = remaining_after_buy
        neg_txt = f" (-{disc*100:.0f}%)" if did else ""
        team.last_action = f"Bought: {item.name} ${item.shop_price:.0f}{neg_txt}"

    def _move_towards(self, team, tx, ty, dt, speed):
        dx, dy = tx - team.x, ty - team.y
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 1e-6:
            return
        step = min(dist, speed * dt)
        team.x += dx / dist * step
        team.y += dy / dist * step

    def reserve_expert_budget(self):
        """Lock in the leftover cash that must be handed to the expert."""
        for team in self.teams:
            team.expert_pick_budget = round(team.budget_left, 2)
            team.budget_left = 0.0
            team.expert_pick_item = None
            team.expert_pick_included = False if team.expert_pick_budget < self.expert_min_budget else None
            team.last_action = f"Reserved ${team.expert_pick_budget:0.0f} for expert"

    def prepare_expert_picks(self):
        """Hand the remaining budget to experts and let them shop within it."""
        self.expert_purchase_events = []  # list of dicts: team, item, budget
        for team in self.teams:
            leftover = round(team.expert_pick_budget if team.expert_pick_budget else team.budget_left, 2)
            team.expert_pick_budget = leftover
            team.budget_left = 0.0
            pick = None
            if leftover >= self.expert_min_budget:
                pick = team.expert.choose_leftover_purchase(self.market, leftover, self.rng)
            team.expert_pick_item = pick
            team.expert_pick_included = False if pick is None else team.expert_pick_included
            if pick:
                self.market.remove_item(pick)
                pick.is_expert_pick = True
                pick.attributes["expert_estimate"] = round(team.expert.estimate_value(pick, self.rng), 2)
                team.last_action = f"Expert shopping with ${leftover:0.0f}"
            else:
                team.last_action = "Expert couldn't find an item"
            self.expert_purchase_events.append({"team": team, "item": pick, "budget": leftover})

    def mark_expert_choice(self, team: Team, include: bool):
        """Record whether a team wants to include their expert item in scoring."""
        if not team.expert_pick_item:
            team.expert_pick_included = False
            return
        team.expert_pick_included = include
        if include:
            team.last_action = f"Including expert pick: {team.expert_pick_item.name}"
        else:
            team.last_action = "Declined the expert item"

    def expert_choices_done(self) -> bool:
        for team in self.teams:
            if team.expert_pick_item and team.expert_pick_included is None:
                return False
        return True

    def has_included_expert_items(self) -> bool:
        return any(team.expert_pick_included and team.expert_pick_item for team in self.teams)

    def start_appraisal(self):
        # appraise all items (team items + expert pick candidate)
        for team in self.teams:
            for item in team.items_bought:
                item.appraised_value = self.auctioneer.appraise(item, self.rng)
            if team.expert_pick_item:
                team.expert_pick_item.appraised_value = self.auctioneer.appraise(team.expert_pick_item, self.rng)
        self.appraisal_done = True

    def _reset_auction_state(self, lots, label: str, stage: str):
        self.auction_queue = lots
        self.auction_cursor = 0
        self.auction_done = len(lots) == 0
        self.last_sold = None
        self.auction_label = label
        self.auction_stage = stage

    def start_team_auction(self):
        lots: list[AuctionLot] = []
        for team in self.teams:
            team_items = team.team_items
            team_total = len(team_items)
            for idx, item in enumerate(team_items, start=1):
                lots.append(
                    AuctionLot(
                        team=team,
                        item=item,
                        position_in_team=idx,
                        team_total=team_total,
                        is_bonus=False,
                    )
                )
        self._reset_auction_state(lots, "Team items first", "team")

    def start_expert_auction(self):
        lots: list[AuctionLot] = []
        for team in self.teams:
            if team.expert_pick_included and team.expert_pick_item:
                item = team.expert_pick_item
                lots.append(
                    AuctionLot(
                        team=team,
                        item=item,
                        position_in_team=1,
                        team_total=1,
                        is_bonus=True,
                    )
                )
        self._reset_auction_state(lots, "Expert reveal auction", "expert")

    def finalize_auction_sale(self, lot: AuctionLot, sale_price: float):
        """Record the result of an auction lot without advancing RNG twice."""
        lot.item.auction_price = sale_price
        self.last_sold = lot
        self.auction_cursor += 1
        if self.auction_cursor >= len(self.auction_queue):
            self.auction_done = True

    def step_auction(self):
        if self.auction_cursor >= len(self.auction_queue):
            self.auction_done = True
            return
        lot = self.auction_queue[self.auction_cursor]
        sale_price = self.auction_house.sell(lot.item, self.rng)
        self.finalize_auction_sale(lot, sale_price)

    def compute_results(self):
        for team in self.teams:
            compute_team_totals(team)
            team.golden_gavel = golden_gavel(team)
        # winner by profit
        self.winner = max(self.teams, key=lambda t: t.profit)
        self.results_done = True
