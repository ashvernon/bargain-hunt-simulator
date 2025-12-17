import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from constants import TEAM_A, TEAM_B
from models.item import Item
from models.team import Team
from models.episode import Episode
from sim.scoring import compute_team_totals, golden_gavel


def make_item(item_id: int, shop_price: float, auction_price: float, *, category: str = "tools") -> Item:
    return Item(
        item_id=item_id,
        name=f"Item {item_id}",
        category=category,
        era="modern",
        condition=0.7,
        rarity=0.3,
        style_score=0.6,
        true_value=120.0,
        shop_price=shop_price,
        auction_price=auction_price,
    )


def make_team(name: str, color) -> Team:
    return Team(
        name=name,
        color=color,
        budget_start=100.0,
        budget_left=25.0,
        strategy=None,
        expert=None,
        contestants=[],
        x=0,
        y=0,
    )


def test_compute_totals_rolls_up_sale_prices_and_spend():
    team = make_team("Totals", TEAM_A)
    team.items_bought = [
        make_item(1, shop_price=20.0, auction_price=50.0),
        make_item(2, shop_price=30.0, auction_price=0.0),
        make_item(3, shop_price=10.0, auction_price=5.0),
    ]
    expert_pick = make_item(4, shop_price=15.0, auction_price=60.0, category="silverware")
    expert_pick.is_expert_pick = True
    team.expert_pick_item = expert_pick
    team.expert_pick_included = True

    compute_team_totals(team)

    assert team.spend == 75.0
    assert team.revenue == 115.0
    assert team.profit == 40.0


def test_golden_gavel_requires_all_team_profits_and_can_be_shared():
    all_profitable = make_team("Profits", TEAM_A)
    all_profitable.items_bought = [
        make_item(11, 20.0, 40.0),
        make_item(12, 15.0, 30.0),
        make_item(13, 10.0, 25.0),
    ]

    with_loss = make_team("Mixed", TEAM_B)
    with_loss.items_bought = [
        make_item(21, 20.0, 40.0),
        make_item(22, 15.0, 10.0),
        make_item(23, 10.0, 25.0),
    ]

    assert golden_gavel(all_profitable)
    assert not golden_gavel(with_loss)

    also_profitable = make_team("Profits Too", TEAM_B)
    also_profitable.items_bought = [
        make_item(31, 18.0, 38.0),
        make_item(32, 16.0, 28.0),
        make_item(33, 12.0, 26.0),
    ]

    episode = Episode(0, seed=1, play_rect=(0, 0, 0, 0), items_per_team=3, starting_budget=0)
    episode.teams = [all_profitable, also_profitable]
    episode.compute_results()

    assert all(team.golden_gavel for team in episode.teams)
