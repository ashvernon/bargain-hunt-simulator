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

        mood_population = []
        for mood_name, weight in ah_cfg.mood_probs.items():
            mood_population.extend([mood_name] * int(weight * 100))
        mood = rng.choice(mood_population) if mood_population else "mixed"
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
        price = item.true_value * demand * condition_mult * mood_mult * noise
        # Clamp to keep values sane
        price = max(1.0, min(price, item.true_value * ah_cfg.clamp_multiplier))
        return float(round(price, 2))
