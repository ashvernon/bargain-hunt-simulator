from __future__ import annotations

class AuctionHouse:
    def __init__(self, demand_by_category: dict, mood: str = "mixed"):
        self.demand_by_category = demand_by_category
        self.mood = mood

    @classmethod
    def generate(cls, rng):
        # Demand multipliers by category (episode-level)
        cats = ["ceramics", "clocks", "tools", "glassware", "prints", "toys", "silverware", "books"]
        demand = {}
        for c in cats:
            demand[c] = rng.uniform(0.85, 1.25)
        mood = rng.choice(["hot", "cold", "mixed"])
        return cls(demand_by_category=demand, mood=mood)

    def sell(self, item, rng) -> float:
        demand = self.demand_by_category.get(item.category, 1.0)
        condition_mult = 0.65 + 0.75 * item.condition

        if self.mood == "hot":
            mood_mult = 1.08
            sigma = 0.40
        elif self.mood == "cold":
            mood_mult = 0.93
            sigma = 0.33
        else:
            mood_mult = 1.0
            sigma = 0.36

        noise = rng.lognormal(0.0, sigma)
        price = item.true_value * demand * condition_mult * mood_mult * noise
        # Clamp to keep values sane
        price = max(1.0, min(price, item.true_value * 3.5))
        return float(round(price, 2))
