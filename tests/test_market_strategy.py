import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ai.spend_plan import default_spend_plans
from ai.strategy_value import ValueHunterStrategy
from models.episode import Episode
from models.expert import Expert, ExpertProfile
from models.item import Item
from models.market import Market
from models.stall import Stall
from models.team import Team
from sim.rng import RNG


@pytest.fixture
def rng():
    return RNG(42)


def make_item(item_id: int, price: float, true_value: float = 120.0):
    return Item(
        item_id=item_id,
        name=f"Item {item_id}",
        category="misc",
        era="modern",
        condition=0.7,
        rarity=0.3,
        style_score=0.6,
        true_value=true_value,
        shop_price=price,
    )


def make_expert(name: str = "Helper", specialty: str = "tools") -> Expert:
    profile = ExpertProfile(
        id=f"expert_{name.lower()}",
        full_name=name,
        specialty=specialty,
        years_experience=10,
        signature_style="calm mentor",
        appraisal_accuracy=0.8,
        negotiation_skill=0.6,
        risk_appetite=0.5,
        category_bias={specialty: 1.1},
        time_management=0.6,
        trust_factor=0.6,
    )
    return Expert(profile)


def test_spend_plan_keeps_budget_for_future_buys():
    plan = default_spend_plans()[0]  # BIG_TWO_SMALL
    # Buying 70 on the first purchase with a $100 budget should be rejected
    allowed = plan.allows_purchase(
        price=70,
        purchase_index=0,
        budget_start=100,
        budget_left=100,
        remaining_slots=3,
        min_expected_price=10,
    )
    assert not allowed

    allowed_small = plan.allows_purchase(
        price=60,
        purchase_index=0,
        budget_start=100,
        budget_left=100,
        remaining_slots=3,
        min_expected_price=10,
    )
    assert allowed_small


def test_retarget_when_current_stall_too_expensive(rng):
    strategy = ValueHunterStrategy()
    market = Market(
        stalls=[
            Stall(1, "Expensive", (0, 0, 20, 20), "fair", 0.1, 0.05, 0.2, items=[make_item(1, 120)]),
            Stall(2, "Affordable", (100, 0, 20, 20), "fair", 0.1, 0.05, 0.2, items=[make_item(2, 18)]),
        ]
    )

    team = Team(
        "Test",
        (0, 0, 0),
        budget_start=50,
        budget_left=50,
        strategy=strategy,
        expert=make_expert(),
        contestants=[],
        x=0,
        y=0,
    )
    team.spend_plan = default_spend_plans()[2]  # THREE_SMALL for predictable cap

    episode = Episode(0, seed=7, play_rect=(0, 0, 0, 0), items_per_team=3, starting_budget=50)
    episode.rng = rng
    episode.market = market
    episode.teams = [team]

    # Start fixated on the expensive stall
    team.target_stall_id = 1
    episode.update_market_ai(dt=0.1, team_speed=0, buy_radius=5)

    assert team.target_stall_id == 2
    assert team.stall_cooldowns.get(1) is not None


def test_strategy_respects_plan_when_picking_item(rng):
    strategy = ValueHunterStrategy()
    market = Market(
        stalls=[
            Stall(
                1,
                "Mixed",
                (0, 0, 20, 20),
                "fair",
                0.1,
                0.05,
                0.2,
                items=[make_item(1, 25, true_value=150.0), make_item(2, 18, true_value=220.0)],
            )
        ]
    )

    team = Team(
        "Test",
        (0, 0, 0),
        budget_start=50,
        budget_left=50,
        strategy=strategy,
        expert=make_expert(),
        contestants=[],
        x=0,
        y=0,
    )
    team.spend_plan = default_spend_plans()[2]

    pick = strategy.decide_purchase(market, team, market.stalls[0], rng, items_per_team=3)
    assert pick is not None
    assert math.isclose(pick.shop_price, 18)
