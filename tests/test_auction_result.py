from models.auction_result import AuctionRoundResult
from models.item import Item
from models.team import Team


def _make_item(
    item_id: int,
    name: str,
    category: str,
    paid: float,
    appraised: float,
    sold: float,
    is_expert: bool = False,
):
    item = Item(
        item_id=item_id,
        name=name,
        category=category,
        era="modern",
        condition=0.8,
        rarity=0.5,
        style_score=0.6,
        true_value=appraised,
        shop_price=paid,
    )
    item.appraised_value = appraised
    item.auction_price = sold
    item.is_expert_pick = is_expert
    return item


def test_round_result_totals_and_best_worst():
    team = Team("Red", (255, 0, 0), 1000, 400, None, None, [], 0, 0)
    items = [
        _make_item(1, "Silver Teapot", "silverware", paid=120, appraised=180, sold=210),
        _make_item(2, "Art Print", "art", paid=90, appraised=160, sold=130),
        _make_item(3, "Retro Clock", "decor", paid=60, appraised=140, sold=95),
    ]

    result = AuctionRoundResult.from_team(team, items)

    assert result.spent_total == 270
    assert result.sold_total == 435
    assert result.profit_total == 165
    assert round(result.roi, 3) == round(435 / 270 - 1, 3)

    assert result.best_lot.name == "Silver Teapot"
    assert result.worst_lot.name == "Retro Clock"
    assert result.sold_count == 3
    assert result.total_count == 3


def test_round_result_handles_zero_spend():
    team = Team("Blue", (0, 0, 255), 1000, 300, None, None, [], 0, 0)
    freebie = _make_item(4, "Gifted Vase", "ceramics", paid=0, appraised=60, sold=80, is_expert=True)

    result = AuctionRoundResult.from_team(team, [freebie])

    assert result.spent_total == 0
    assert result.sold_total == 80
    assert result.profit_total == 80
    assert result.roi == 0.0
    assert result.best_lot == result.worst_lot
    assert result.lots[0].is_expert_pick is True
