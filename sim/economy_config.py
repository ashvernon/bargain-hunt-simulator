"""Centralized economy tuning values for the simulator.

These numbers are tuned for more realistic outcomes: occasional
losses, rarer Golden Gavels, and less automatic profit drift.
"""

SHOP_PRICING = {
    # “Fair” is closer to true value with some overpay risk.
    "fair": (0.75, 1.05),
    # Overpriced should feel meaningfully risky.
    "overpriced": (0.95, 1.45),
    # Chaotic stays wild for special episodes.
    "chaotic": (0.60, 1.60),
    "min_price": 5.0,
}

NEGOTIATION = {
    "max_chance": 0.65,
    "discount_min": None,
    "discount_max": None,
    "discount_floor": 0.0,
    "discount_ceiling": 0.35,
}

AUCTIONEER = {
    "sigma_floor": 0.03,
    "sigma_scale": 0.55,
    "bias_by_category": {},
    "default_accuracy": 0.80,
    "appraisal_ratio_cap": 1.40,
}

AUCTION_HOUSE = {
    "categories": [
        "ceramics",
        "clocks",
        "tools",
        "glassware",
        "prints",
        "toys",
        "silverware",
        "books",
    ],
    "demand_range": (0.80, 1.15),
    "mood_probs": {"hot": 0.25, "cold": 0.30, "mixed": 0.45},
    "moods": {
        "hot": {"multiplier": 1.01, "sigma": 0.26},
        "cold": {"multiplier": 0.86, "sigma": 0.30},
        "mixed": {"multiplier": 1.00, "sigma": 0.28},
    },
    "clamp_multiplier": 2.0,
    "condition_base": 0.65,
    "condition_scale": 0.75,
}

TRUE_VALUE = {
    "fallback_sigma": 0.35,
}

GAVEL = {
    "profit_threshold": 350.0,
    "probability": 0.18,
}
