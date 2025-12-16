from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class SpendPlanName(str, Enum):
    BIG_TWO_SMALL = "big_two_small"
    ONE_MED_TWO_SMALL = "one_med_two_small"
    THREE_SMALL = "three_small"


@dataclass(frozen=True)
class SpendPlan:
    name: SpendPlanName
    price_caps: Sequence[float]

    def max_price_for_purchase(self, purchase_index: int, budget_start: float) -> float:
        capped_index = min(purchase_index, len(self.price_caps) - 1)
        cap_ratio = self.price_caps[capped_index]
        return budget_start * cap_ratio

    def allows_purchase(
        self,
        price: float,
        purchase_index: int,
        budget_start: float,
        budget_left: float,
        remaining_slots: int,
        min_expected_price: float,
    ) -> bool:
        if price > budget_left:
            return False

        price_cap = self.max_price_for_purchase(purchase_index, budget_start)
        if price > price_cap and remaining_slots > 1:
            return False

        budget_after = budget_left - price
        slots_after_buy = remaining_slots - 1
        reserved = max(0, slots_after_buy) * min_expected_price
        if budget_after < reserved - 1e-6:
            return False

        return True


def default_spend_plans() -> list[SpendPlan]:
    return [
        SpendPlan(SpendPlanName.BIG_TWO_SMALL, price_caps=(0.68, 0.22, 0.22)),
        SpendPlan(SpendPlanName.ONE_MED_TWO_SMALL, price_caps=(0.52, 0.26, 0.26)),
        SpendPlan(SpendPlanName.THREE_SMALL, price_caps=(0.38, 0.38, 0.38)),
    ]


def pick_spend_plan(rng) -> SpendPlan:
    plans = default_spend_plans()
    return rng.choice(plans)
