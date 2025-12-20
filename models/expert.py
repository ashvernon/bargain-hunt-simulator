from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class ExpertProfile:
    id: str
    full_name: str
    specialty: str
    years_experience: int
    signature_style: str

    appraisal_accuracy: float
    negotiation_skill: float
    risk_appetite: float
    image_path: str | None = None
    category_bias: Dict[str, float] = field(default_factory=dict)
    time_management: float = 0.5
    trust_factor: float = 0.55

    catchphrase: str | None = None
    mood_baseline: str | None = None

    @classmethod
    def from_dict(cls, data: Dict) -> "ExpertProfile":
        return cls(
            id=data["id"],
            full_name=data["full_name"],
            specialty=data["specialty"],
            years_experience=int(data.get("years_experience", 1)),
            signature_style=data.get("signature_style", ""),
            appraisal_accuracy=float(data.get("appraisal_accuracy", 0.75)),
            negotiation_skill=float(data.get("negotiation_skill", 0.5)),
            risk_appetite=float(data.get("risk_appetite", 0.5)),
            image_path=data.get("image_path"),
            category_bias=dict(data.get("category_bias", {})),
            time_management=float(data.get("time_management", 0.5)),
            trust_factor=float(data.get("trust_factor", 0.55)),
            catchphrase=data.get("catchphrase"),
            mood_baseline=data.get("mood_baseline"),
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "specialty": self.specialty,
            "years_experience": self.years_experience,
            "signature_style": self.signature_style,
            "appraisal_accuracy": self.appraisal_accuracy,
            "negotiation_skill": self.negotiation_skill,
            "risk_appetite": self.risk_appetite,
            "image_path": self.image_path,
            "category_bias": self.category_bias,
            "time_management": self.time_management,
            "trust_factor": self.trust_factor,
            "catchphrase": self.catchphrase,
            "mood_baseline": self.mood_baseline,
        }


class Expert:
    def __init__(self, profile: ExpertProfile, effect_strength: float = 1.0):
        self.profile = profile
        self.effect_strength = effect_strength
        self.name = profile.full_name
        self.specialty = profile.specialty
        self.signature_style = profile.signature_style
        self.image_path = profile.image_path
        self.appraisal_accuracy = _clamp01(profile.appraisal_accuracy)
        self.negotiation_skill = _clamp01(profile.negotiation_skill)
        self.risk_appetite = _clamp01(profile.risk_appetite)
        self.time_management = _clamp01(profile.time_management)
        self.trust_factor = _clamp01(profile.trust_factor)
        self.category_bias = dict(profile.category_bias or {})
        if self.specialty not in self.category_bias:
            self.category_bias[self.specialty] = 1.08

    @classmethod
    def from_profile(cls, profile: ExpertProfile, effect_strength: float = 1.0) -> "Expert":
        return cls(profile=profile, effect_strength=effect_strength)

    @property
    def negotiation_bonus(self) -> float:
        base = 0.02 + 0.12 * self.negotiation_skill
        return base * self.effect_strength

    @property
    def consultation_time_factor(self) -> float:
        # High time management shortens deliberation, low values slow the team down.
        return max(0.6, 1.15 - self.time_management * 0.45)

    def adjust_target_margin(self, target: float) -> float:
        # Risk seekers accept thinner margins while cautious experts push for safer picks.
        swing = (self.risk_appetite - 0.5) * 0.4 * self.effect_strength
        return max(1.0, target * (1.0 - swing))

    def _category_multiplier(self, item) -> float:
        bias = self.category_bias.get(item.category, 1.0)
        risk_push = 1.0 + (self.risk_appetite - 0.5) * 0.18 * self.effect_strength
        return bias * risk_push

    def _optimism_multiplier(self) -> float:
        return 1.0 + (self.risk_appetite - 0.5) * 0.14 * self.effect_strength

    def _expected_negotiated_price(self, item) -> float:
        base_discount = 0.04 + 0.1 * self.negotiation_skill
        success_chance = 0.35 + 0.4 * self.negotiation_skill
        expected_discount = min(0.3, base_discount * success_chance * self.effect_strength)
        return max(1.0, round(item.shop_price * (1.0 - expected_discount), 2))

    def _negotiate_price(self, item, rng) -> float:
        success_chance = min(0.95, 0.35 + 0.45 * self.negotiation_skill * self.effect_strength)
        if rng.random() < success_chance:
            disc = rng.uniform(0.03, 0.08 + 0.12 * self.negotiation_skill)
            disc *= self.effect_strength
            disc = min(0.4, disc)
            item.shop_price = round(item.shop_price * (1.0 - disc), 2)
            item.was_negotiated = True
            return disc
        item.was_negotiated = False
        return 0.0

    def estimate_value(self, item, rng) -> float:
        # Better accuracy => tighter noise around true value
        noise_sigma = max(0.05, (1.0 - self.appraisal_accuracy) * 0.6)
        est = item.true_value * rng.lognormal(0.0, noise_sigma)
        est *= self._category_multiplier(item)
        est *= self._optimism_multiplier()
        return float(est)

    def appraise(self, item, rng) -> float:
        # Appraisal is an estimate with similar mechanics, slightly more conservative
        est = self.estimate_value(item, rng) * 0.95
        return float(round(est, 2))

    def recommend_from_stall(self, stall, budget_left, rng):
        # Choose the best "expected margin" item in this stall that is affordable.
        best = None
        best_score = float("-inf")
        for it in stall.items:
            expected_price = self._expected_negotiated_price(it)
            if expected_price > budget_left:
                continue
            est = self.estimate_value(it, rng)
            margin = est - expected_price
            specialty_pull = 1.2 if it.category == self.specialty else 1.0
            risk_push = 1.0 + (self.risk_appetite - 0.5) * 0.6
            score = margin * risk_push * specialty_pull + it.condition * 4.0
            if score > best_score:
                best_score = score
                best = it
        return best

    def choose_leftover_purchase(self, market, budget_left, rng):
        # Rule: only from remaining stall inventory and must be affordable with leftover.
        candidates = [it for it in market.all_remaining_items() if self._expected_negotiated_price(it) <= budget_left]
        if not candidates:
            return None
        best = None
        best_score = float("-inf")
        for it in candidates:
            est = self.estimate_value(it, rng)
            expected_price = self._expected_negotiated_price(it)
            margin = est - expected_price
            specialty_pull = 1.15 if it.category == self.specialty else 1.0
            risk_push = 1.0 + (self.risk_appetite - 0.5) * 0.8
            speed_bonus = (0.6 + self.time_management) * 0.5
            score = margin * risk_push * specialty_pull + speed_bonus + rng.uniform(0, 1.5)
            if score > best_score:
                best_score, best = score, it

        if best:
            discount = self._negotiate_price(best, rng)
            if discount > 0:
                best.attributes["expert_discount"] = round(discount * 100, 1)
        return best
