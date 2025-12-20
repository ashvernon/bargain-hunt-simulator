from __future__ import annotations

from sim.balance_config import BalanceConfig


class AuctionHouse:
    def __init__(self, demand_by_category: dict, mood: str = "mixed"):
        self.demand_by_category = demand_by_category
        self.mood = mood

    @classmethod
    def generate(cls, rng, cfg: BalanceConfig | None = None):
        cfg = cfg or BalanceConfig()
        ah_cfg = cfg.auction_house
        # Demand multipliers by category (episode-level)
        cats = ah_cfg.categories
        demand = {}
        for c in cats:
            demand[c] = rng.uniform(*ah_cfg.demand_range)

        total_weight = sum(ah_cfg.mood_probs.values())
        if total_weight > 0:
            draw = rng.random() * total_weight
            cumulative = 0.0
            mood = "mixed"
            for mood_name, weight in ah_cfg.mood_probs.items():
                cumulative += weight
                if draw <= cumulative:
                    mood = mood_name
                    break
        else:
            mood = "mixed"
        return cls(demand_by_category=demand, mood=mood)

    def sell(self, item, rng, cfg: BalanceConfig | None = None) -> float:
        cfg = cfg or BalanceConfig()
        ah_cfg = cfg.auction_house

        demand = self.demand_by_category.get(item.category, 1.0)
        condition_mult = ah_cfg.condition_base + ah_cfg.condition_scale * item.condition

        mood_tuning = ah_cfg.moods.get(self.mood, ah_cfg.moods.get("mixed"))
        mood_mult = mood_tuning.multiplier
        sigma = mood_tuning.sigma

        noise = rng.lognormal(0.0, sigma)
        multiplier = demand * condition_mult * mood_mult * noise
        clamp_hi = ah_cfg.clamp_multiplier
        clamp_lo = 1.0 / clamp_hi
        multiplier = max(clamp_lo, min(multiplier, clamp_hi))
        price = max(1.0, item.true_value * multiplier)
        return float(round(price, 2))
