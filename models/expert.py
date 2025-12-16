from __future__ import annotations

class Expert:
    def __init__(self, name: str, accuracy: float = 0.78, negotiation_bonus: float = 0.07, bias=None):
        self.name = name
        self.accuracy = accuracy
        self.negotiation_bonus = negotiation_bonus
        self.bias = bias or {}

    def estimate_value(self, item, rng) -> float:
        # Better accuracy => tighter noise around true value
        noise_sigma = max(0.05, (1.0 - self.accuracy) * 0.65)
        est = item.true_value * rng.lognormal(0.0, noise_sigma)
        est *= self.bias.get(item.category, 1.0)
        return float(est)

    def appraise(self, item, rng) -> float:
        # Appraisal is an estimate with similar mechanics, slightly more conservative
        est = self.estimate_value(item, rng) * 0.95
        return float(round(est, 2))

    def recommend_from_stall(self, stall, budget_left, rng):
        # Choose the best "expected margin" item in this stall that is affordable.
        best = None
        best_margin = float("-inf")
        for it in stall.items:
            if it.shop_price > budget_left:
                continue
            est = self.estimate_value(it, rng)
            margin = est - it.shop_price
            if margin > best_margin:
                best_margin = margin
                best = it
        return best

    def choose_leftover_purchase(self, market, budget_left, rng):
        # Rule: only from remaining stall inventory and must be affordable with leftover.
        candidates = [it for it in market.all_remaining_items() if it.shop_price <= budget_left]
        if not candidates:
            return None
        best = None
        best_score = float("-inf")
        for it in candidates:
            est = self.estimate_value(it, rng)
            score = (est - it.shop_price) + 6.0 * rng.random()  # tiny spice
            if score > best_score:
                best_score, best = score, it
        return best
