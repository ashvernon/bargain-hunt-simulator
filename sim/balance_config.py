from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ShopPricingConfig:
    fair: tuple[float, float] = (0.55, 0.9)
    overpriced: tuple[float, float] = (0.85, 1.25)
    chaotic: tuple[float, float] = (0.45, 1.45)
    min_price: float = 5.0


@dataclass
class NegotiationConfig:
    max_chance: float = 0.95
    discount_min: float | None = None
    discount_max: float | None = None
    discount_floor: float = 0.0
    discount_ceiling: float = 0.85


@dataclass
class AuctioneerConfig:
    sigma_floor: float = 0.03
    sigma_scale: float = 0.55
    bias_by_category: dict[str, float] = field(default_factory=dict)
    default_accuracy: float = 0.82
    appraisal_ratio_cap: float = 1.55


@dataclass
class TrueValueConfig:
    fallback_sigma: float = 0.35


@dataclass
class MoodTuning:
    multiplier: float
    sigma: float


@dataclass
class AuctionHouseConfig:
    categories: list[str] = field(
        default_factory=lambda: [
            "ceramics",
            "clocks",
            "tools",
            "glassware",
            "prints",
            "toys",
            "silverware",
            "books",
        ]
    )
    demand_range: tuple[float, float] = (0.85, 1.25)
    mood_probs: dict[str, float] = field(
        default_factory=lambda: {"hot": 1.0, "cold": 1.0, "mixed": 1.0}
    )
    moods: dict[str, MoodTuning] = field(
        default_factory=lambda: {
            "hot": MoodTuning(multiplier=1.03, sigma=0.30),
            "cold": MoodTuning(multiplier=0.9, sigma=0.26),
            "mixed": MoodTuning(multiplier=1.0, sigma=0.28),
        }
    )
    clamp_multiplier: float = 2.4
    condition_base: float = 0.65
    condition_scale: float = 0.75


@dataclass
class GavelConfig:
    profit_threshold: float = 225.0
    probability: float = 0.25


@dataclass
class BalanceConfig:
    shop_pricing: ShopPricingConfig = field(default_factory=ShopPricingConfig)
    negotiation: NegotiationConfig = field(default_factory=NegotiationConfig)
    auctioneer: AuctioneerConfig = field(default_factory=AuctioneerConfig)
    auction_house: AuctionHouseConfig = field(default_factory=AuctionHouseConfig)
    true_value: TrueValueConfig = field(default_factory=TrueValueConfig)
    gavel: GavelConfig = field(default_factory=GavelConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, path: str | Path):
        Path(path).write_text(self.to_json_str(), encoding="utf-8")

    def to_json_str(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BalanceConfig":
        def _tuple(vals, default):
            return tuple(vals) if vals is not None else tuple(default)

        def _build_moods(moods: dict[str, Any]) -> dict[str, MoodTuning]:
            built: dict[str, MoodTuning] = {}
            for key, value in moods.items():
                built[key] = MoodTuning(
                    multiplier=value.get("multiplier", 1.0),
                    sigma=value.get("sigma", AuctionHouseConfig().moods["mixed"].sigma),
                )
            return built

        shop_pricing = ShopPricingConfig(
            fair=_tuple(data.get("shop_pricing", {}).get("fair"), ShopPricingConfig().fair),
            overpriced=_tuple(
                data.get("shop_pricing", {}).get("overpriced"), ShopPricingConfig().overpriced
            ),
            chaotic=_tuple(
                data.get("shop_pricing", {}).get("chaotic"), ShopPricingConfig().chaotic
            ),
            min_price=data.get("shop_pricing", {}).get("min_price", ShopPricingConfig().min_price),
        )

        negotiation_data = data.get("negotiation", {})
        negotiation = NegotiationConfig(
            max_chance=negotiation_data.get("max_chance", NegotiationConfig().max_chance),
            discount_min=negotiation_data.get("discount_min", NegotiationConfig().discount_min),
            discount_max=negotiation_data.get("discount_max", NegotiationConfig().discount_max),
            discount_floor=negotiation_data.get(
                "discount_floor", NegotiationConfig().discount_floor
            ),
            discount_ceiling=negotiation_data.get(
                "discount_ceiling", NegotiationConfig().discount_ceiling
            ),
        )

        auctioneer_data = data.get("auctioneer", {})
        auctioneer = AuctioneerConfig(
            sigma_floor=auctioneer_data.get("sigma_floor", AuctioneerConfig().sigma_floor),
            sigma_scale=auctioneer_data.get("sigma_scale", AuctioneerConfig().sigma_scale),
            bias_by_category=auctioneer_data.get(
                "bias_by_category", AuctioneerConfig().bias_by_category
            ),
            default_accuracy=auctioneer_data.get(
                "default_accuracy", AuctioneerConfig().default_accuracy
            ),
            appraisal_ratio_cap=auctioneer_data.get(
                "appraisal_ratio_cap", AuctioneerConfig().appraisal_ratio_cap
            ),
        )

        true_value = TrueValueConfig(
            fallback_sigma=data.get("true_value", {}).get(
                "fallback_sigma", TrueValueConfig().fallback_sigma
            )
        )

        auction_house_data = data.get("auction_house", {})
        auction_house = AuctionHouseConfig(
            categories=auction_house_data.get("categories", AuctionHouseConfig().categories),
            demand_range=_tuple(
                auction_house_data.get("demand_range"), AuctionHouseConfig().demand_range
            ),
            mood_probs=auction_house_data.get("mood_probs", AuctionHouseConfig().mood_probs),
            moods=_build_moods(auction_house_data.get("moods", AuctionHouseConfig().moods)),
            clamp_multiplier=auction_house_data.get(
                "clamp_multiplier", AuctionHouseConfig().clamp_multiplier
            ),
            condition_base=auction_house_data.get(
                "condition_base", AuctionHouseConfig().condition_base
            ),
            condition_scale=auction_house_data.get(
                "condition_scale", AuctionHouseConfig().condition_scale
            ),
        )

        gavel_data = data.get("gavel", {})
        gavel = GavelConfig(
            profit_threshold=gavel_data.get("profit_threshold", GavelConfig().profit_threshold),
            probability=gavel_data.get("probability", GavelConfig().probability),
        )

        return cls(
            shop_pricing=shop_pricing,
            negotiation=negotiation,
            auctioneer=auctioneer,
            auction_house=auction_house,
            true_value=true_value,
            gavel=gavel,
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "BalanceConfig":
        import json

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)
