from __future__ import annotations
from dataclasses import dataclass
from sim.rng import RNG
from models.market import Market
from models.team import Team
from models.expert import Expert
from models.auction_house import AuctionHouse
from sim.pricing import negotiate
from sim.scoring import compute_team_totals, golden_gavel
from ai.strategy_value import ValueHunterStrategy
from ai.strategy_risk import RiskAverseStrategy

@dataclass
class Episode:
    ep_idx: int
    seed: int
    play_rect: tuple[int,int,int,int]
    items_per_team: int
    starting_budget: float

    def setup(self):
        self.rng = RNG(self.seed)
        self.market = Market.generate(self.rng, self.play_rect)
        self.auction_house = AuctionHouse.generate(self.rng)

        # Experts
        exp_a = Expert("Natasha", accuracy=0.80, negotiation_bonus=0.08, bias={"glassware": 1.06})
        exp_b = Expert("Raj", accuracy=0.76, negotiation_bonus=0.06, bias={"tools": 1.08})

        # Teams
        x0,y0,w,h = self.play_rect
        self.teams = [
            Team("Team A", (220,120,120), self.starting_budget, self.starting_budget, ValueHunterStrategy(), exp_a, x0+90, y0+h/2),
            Team("Team B", (120,200,150), self.starting_budget, self.starting_budget, RiskAverseStrategy(), exp_b, x0+w-120, y0+h/2),
        ]

        self.appraisal_done = False
        self.auction_done = False
        self.results_done = False
        self.auction_queue = []  # list of (team, item)
        self.auction_cursor = 0

    def update_market_ai(self, dt: float, team_speed: float, buy_radius: float):
        # Simple AI: pick a target stall; move; when close, attempt to buy.
        for team in self.teams:
            if not team.can_buy_more(self.items_per_team):
                team.last_action = "Done shopping"
                continue

            # choose target stall if none / empty
            target = None
            if team.target_stall_id is not None:
                target = next((s for s in self.market.stalls if s.stall_id == team.target_stall_id), None)
                if target and not target.items:
                    target = None

            if target is None:
                target = team.strategy.pick_target_stall(self.market, team, self.rng)
                team.target_stall_id = target.stall_id if target else None

            if not target:
                team.last_action = "No stalls left"
                continue

            tx, ty = target.center()
            # move
            self._move_towards(team, tx, ty, dt, team_speed)

            # purchase if close enough
            if team.distance_to(tx, ty) <= buy_radius:
                item = team.strategy.decide_purchase(self.market, team, target, self.rng)
                if item:
                    # negotiate (expert helps)
                    did, disc = negotiate(item, self.rng, target.discount_chance, target.discount_min, target.discount_max, expert_bonus=team.expert.negotiation_bonus)
                    item.was_negotiated = did
                    if item.shop_price <= team.budget_left:
                        target.items.remove(item)
                        team.items_bought.append(item)
                        team.budget_left = round(team.budget_left - item.shop_price, 2)
                        neg_txt = f" (-{disc*100:.0f}%)" if did else ""
                        team.last_action = f"Bought: {item.name} ${item.shop_price:.0f}{neg_txt}"
                    else:
                        team.last_action = "Couldn't afford after negotiation"
                else:
                    team.last_action = "Expert says: keep looking"

    def _move_towards(self, team, tx, ty, dt, speed):
        dx, dy = tx - team.x, ty - team.y
        dist = (dx*dx + dy*dy) ** 0.5
        if dist < 1e-6:
            return
        step = min(dist, speed * dt)
        team.x += dx / dist * step
        team.y += dy / dist * step

    def finish_market_expert_leftover_purchase(self):
        """Queue expert leftover purchase proposals.

        Each expert proposes an item based on the team's leftover budget. The
        proposal must later be accepted or declined by the player/UI.
        """
        self.expert_purchase_events = []  # list of dicts: team, item, leftover_before, decision
        for team in self.teams:
            leftover = team.budget_left
            pick = team.expert.choose_leftover_purchase(self.market, leftover, self.rng)
            decision = "no_pick" if pick is None else None
            self.expert_purchase_events.append({
                "team": team,
                "item": pick,
                "leftover_before": leftover,
                "decision": decision,
            })

    def resolve_expert_purchase(self, idx: int, accept: bool):
        """Apply a decision for a proposed expert purchase."""
        event = self.expert_purchase_events[idx]
        if event["decision"] is not None:
            return

        team = event["team"]
        item = event["item"]
        if not item:
            event["decision"] = "no_pick"
            return

        if accept:
            self.market.remove_item(item)
            item.is_expert_pick = True
            team.items_bought.append(item)
            team.budget_left = 0.0
            team.last_action = f"Expert bought: {item.name}"
            event["decision"] = "accepted"
        else:
            team.last_action = "Declined expert pick"
            event["decision"] = "declined"

    def expert_purchases_done(self) -> bool:
        return all(evt["decision"] is not None for evt in getattr(self, "expert_purchase_events", []))

    def start_appraisal(self):
        # appraise all items (team items + expert pick)
        for team in self.teams:
            for item in team.items_bought:
                item.appraised_value = team.expert.appraise(item, self.rng)
        self.appraisal_done = True

    def start_auction(self):
        self.auction_queue = []
        for team in self.teams:
            for item in team.items_bought:
                self.auction_queue.append((team, item))
        # Shuffle order for show drama
        self.rng.shuffle(self.auction_queue)
        self.auction_cursor = 0
        self.auction_done = False
        self.last_sold = None

    def step_auction(self):
        if self.auction_cursor >= len(self.auction_queue):
            self.auction_done = True
            return
        team, item = self.auction_queue[self.auction_cursor]
        item.auction_price = self.auction_house.sell(item, self.rng)
        self.last_sold = (team, item)
        self.auction_cursor += 1
        if self.auction_cursor >= len(self.auction_queue):
            self.auction_done = True

    def compute_results(self):
        for team in self.teams:
            compute_team_totals(team)
            team.golden_gavel = golden_gavel(team)
        # winner by profit
        self.winner = max(self.teams, key=lambda t: t.profit)
        self.results_done = True
