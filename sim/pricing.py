from __future__ import annotations

from sim.balance_config import BalanceConfig


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def clamp_appraisal(value: float, item, cfg: BalanceConfig) -> float:
    """Clamp appraisal estimates to avoid extreme over-valuations.

    The cap is based on the item's true value to prevent runaway ratios from
    noisy draws while still scaling with expensive items.
    """
    cap = cfg.auctioneer.appraisal_ratio_cap
    baseline = max(getattr(item, "true_value", 1.0), 1.0)
    max_allowed = baseline * cap
    return _clamp(value, 1.0, max_allowed)


def set_shop_price(item, rng, pricing_style: str, cfg: BalanceConfig | None = None):
    # Price as a noisy fraction of true value
    cfg = cfg or BalanceConfig()
    pricing_cfg = cfg.shop_pricing

    if pricing_style == "fair":
        frac = rng.uniform(*pricing_cfg.fair)
    elif pricing_style == "overpriced":
        frac = rng.uniform(*pricing_cfg.overpriced)
    else:  # "chaotic"
        frac = rng.uniform(*pricing_cfg.chaotic)

    item.shop_price = max(pricing_cfg.min_price, round(item.true_value * frac, 2))


def negotiate(
    item,
    rng,
    base_chance: float,
    min_disc: float,
    max_disc: float,
    expert_bonus: float = 0.0,
    cfg: BalanceConfig | None = None,
):
    cfg = cfg or BalanceConfig()
    neg_cfg = cfg.negotiation

    chance = min(neg_cfg.max_chance, base_chance + expert_bonus)

    lo = min_disc if neg_cfg.discount_min is None else max(min_disc, neg_cfg.discount_min)
    hi = max_disc if neg_cfg.discount_max is None else min(max_disc, neg_cfg.discount_max)
    lo = _clamp(lo, neg_cfg.discount_floor, neg_cfg.discount_ceiling)
    hi = _clamp(hi, neg_cfg.discount_floor, neg_cfg.discount_ceiling)
    hi = max(hi, lo)

    if rng.random() < chance:
        disc = rng.uniform(lo, hi)
        item.shop_price = round(item.shop_price * (1.0 - disc), 2)
        return True, disc
    return False, 0.0
