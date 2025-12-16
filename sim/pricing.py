from __future__ import annotations

def set_shop_price(item, rng, pricing_style: str):
    # Price as a noisy fraction of true value
    if pricing_style == "fair":
        frac = rng.uniform(0.55, 0.9)
    elif pricing_style == "overpriced":
        frac = rng.uniform(0.85, 1.25)
    else:  # "chaotic"
        frac = rng.uniform(0.45, 1.45)

    item.shop_price = max(5.0, round(item.true_value * frac, 2))

def negotiate(item, rng, base_chance: float, min_disc: float, max_disc: float, expert_bonus: float = 0.0):
    chance = min(0.95, base_chance + expert_bonus)
    if rng.random() < chance:
        disc = rng.uniform(min_disc, max_disc)
        item.shop_price = round(item.shop_price * (1.0 - disc), 2)
        return True, disc
    return False, 0.0
