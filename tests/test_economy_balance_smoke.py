import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.auction_house import AuctionHouse
from models.auctioneer import Auctioneer
from sim.balance_config import BalanceConfig
from sim.item_factory import ItemFactory
from sim.pricing import negotiate, set_shop_price
from sim.rng import RNG


def test_economy_balance_smoke_bounds_and_moods():
    cfg = BalanceConfig()
    rng = RNG(34)
    factory = ItemFactory.with_default_db()
    auctioneer = Auctioneer(name="Balance Checker")

    mood_counts = {name: 0 for name in cfg.auction_house.moods.keys()}
    discounts: list[float] = []
    profits: list[float] = []

    total_attempts = 0
    negotiation_success = 0

    for idx in range(240):
        item = factory.make_item(rng, idx + 1)
        set_shop_price(item, rng, "fair", cfg=cfg)
        did, disc = negotiate(
            item,
            rng,
            base_chance=0.18,
            min_disc=0.05,
            max_disc=0.20,
            expert_bonus=0.0,
            cfg=cfg,
        )
        total_attempts += 1
        if did:
            negotiation_success += 1
            discounts.append(disc)

        auction_house = AuctionHouse.generate(rng, cfg=cfg)
        mood_counts[auction_house.mood] = mood_counts.get(auction_house.mood, 0) + 1

        item.appraised_value = auctioneer.appraise(item, rng, cfg=cfg)
        item.auction_price = auction_house.sell(item, rng, cfg=cfg)
        profits.append(item.auction_price - item.shop_price)

        assert item.auction_price <= item.true_value * cfg.auction_house.clamp_multiplier + 1e-6
        assert item.appraised_value <= item.true_value * cfg.auctioneer.appraisal_ratio_cap + 1e-6

    assert all(count > 0 for count in mood_counts.values())

    assert all(cfg.negotiation.discount_floor <= d <= cfg.negotiation.discount_ceiling for d in discounts)
    assert negotiation_success > 0
    assert negotiation_success < total_attempts

    assert any(p > 0 for p in profits)
    assert any(p < 0 for p in profits)
