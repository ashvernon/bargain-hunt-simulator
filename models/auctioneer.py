from __future__ import annotations


class Auctioneer:
    """Provides auction-house valuations for items.

    This role is intentionally separate from the shopping experts so that
    appraisal accuracy can differ from the estimates used during the hunt.
    """

    def __init__(self, name: str, accuracy: float = 0.84, bias: dict | None = None):
        self.name = name
        self.accuracy = accuracy
        self.bias = bias or {}

    def appraise(self, item, rng) -> float:
        # Higher accuracy means a tighter distribution around the true value.
        noise_sigma = max(0.03, (1.0 - self.accuracy) * 0.55)
        est = item.true_value * rng.lognormal(0.0, noise_sigma)
        est *= self.bias.get(item.category, 1.0)
        return float(round(est, 2))
