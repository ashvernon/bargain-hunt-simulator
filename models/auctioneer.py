from __future__ import annotations

from sim.balance_config import BalanceConfig


class Auctioneer:
    """Provides auction-house valuations for items.

    This role is intentionally separate from the shopping experts so that
    appraisal accuracy can differ from the estimates used during the hunt.
    """

    def __init__(self, name: str, accuracy: float = 0.84, bias: dict | None = None):
        self.name = name
        self.accuracy = accuracy
        self.bias = bias or {}

    def appraise(self, item, rng, cfg: BalanceConfig | None = None) -> float:
        cfg = cfg or BalanceConfig()
        auctioneer_cfg = cfg.auctioneer
        accuracy = self.accuracy or auctioneer_cfg.default_accuracy

        # Higher accuracy means a tighter distribution around the true value.
        noise_sigma = max(auctioneer_cfg.sigma_floor, (1.0 - accuracy) * auctioneer_cfg.sigma_scale)
        est = item.true_value * rng.lognormal(0.0, noise_sigma)
        est *= self.bias.get(item.category, auctioneer_cfg.bias_by_category.get(item.category, 1.0))
        return float(round(est, 2))
