"""Centralized economy tuning values for the simulator.

These values are drawn from the latest headless balance run
(seed=34, pricing_style="fair") to keep gameplay consistent and
avoid hardcoding numbers across modules.
"""

SHOP_PRICING = {
    "fair": (0.55, 0.90),
    "overpriced": (0.85, 1.25),
    "chaotic": (0.45, 1.45),
    "min_price": 5.0,
}

NEGOTIATION = {
    "max_chance": 0.95,
    "discount_floor": 0.0,
    "discount_ceiling": 0.85,
    # Optional overrides for callers to clamp custom ranges.
    "discount_min": None,
    "discount_max": None,
}

AUCTIONEER = {
    "default_accuracy": 0.82,
    "sigma_floor": 0.03,
    "sigma_scale": 0.55,
    "appraisal_ratio_cap": 1.55,
    "bias_by_category": {},
}

AUCTION_HOUSE = {
    "demand_min": 0.85,
    "demand_max": 1.25,
    "moods": {
        "hot": {"multiplier": 1.03, "sigma": 0.30},
        "cold": {"multiplier": 0.90, "sigma": 0.26},
        "mixed": {"multiplier": 1.00, "sigma": 0.28},
    },
    "mood_probs": {"hot": 1.0, "cold": 1.0, "mixed": 1.0},  # normalized at runtime
    "clamp_multiplier": 2.4,
    "condition_base": 0.65,
    "condition_scale": 0.75,
}

GAVEL = {
    "profit_threshold": 225.0,
    "probability": 0.25,
}
