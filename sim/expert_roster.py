from __future__ import annotations

import json
from pathlib import Path
from typing import List, Sequence

from models.expert import Expert, ExpertProfile
from sim.rng import RNG

_ROSTER_CACHE: list[ExpertProfile] | None = None


def load_expert_roster(
    path: str,
    expected_size: int,
    *,
    regen_allowed: bool = False,
    force_regen: bool = False,
    seed: int = 2024,
) -> list[ExpertProfile]:
    """Load or generate the persistent expert roster.

    If `force_regen` is True or the file is missing and regeneration is allowed,
    a deterministic roster is generated and written to disk. The roster is cached
    so subsequent calls avoid re-reading the file.
    """

    global _ROSTER_CACHE
    if _ROSTER_CACHE is not None and not force_regen:
        return _ROSTER_CACHE

    roster_path = Path(path)
    if force_regen or (regen_allowed and not roster_path.exists()):
        profiles = _generate_roster(size=expected_size, seed=seed)
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps([p.to_dict() for p in profiles], indent=2))
        _ROSTER_CACHE = profiles
        return profiles

    if not roster_path.exists():
        raise FileNotFoundError(f"Expert roster not found at {roster_path}. Set --regen-experts to create one.")

    profiles = [ExpertProfile.from_dict(entry) for entry in json.loads(roster_path.read_text())]
    if len(profiles) != expected_size:
        raise ValueError(f"Expected {expected_size} experts, found {len(profiles)} in {roster_path}")

    _ROSTER_CACHE = profiles
    return profiles


def assign_episode_experts(
    rng: RNG,
    roster: Sequence[ExpertProfile],
    *,
    count: int = 2,
    effect_strength: float = 1.0,
) -> List[Expert]:
    """Pick distinct experts for an episode, mixing safe and bold styles."""
    if count > len(roster):
        raise ValueError("Cannot assign more experts than available in the roster")

    ordered = list(roster)
    rng.shuffle(ordered)

    if count == 2:
        cautious = [p for p in ordered if p.risk_appetite < 0.5]
        bold = [p for p in ordered if p.risk_appetite >= 0.5]
        if cautious and bold:
            selected_profiles = [rng.choice(cautious), rng.choice(bold)]
        else:
            selected_profiles = ordered[:2]
    else:
        selected_profiles = ordered[:count]

    seen = set()
    unique_profiles = []
    for profile in selected_profiles:
        if profile.id in seen:
            continue
        unique_profiles.append(profile)
        seen.add(profile.id)
        if len(unique_profiles) == count:
            break

    if len(unique_profiles) < count:
        remaining = [p for p in ordered if p.id not in seen]
        unique_profiles.extend(remaining[: count - len(unique_profiles)])

    return [Expert.from_profile(profile, effect_strength=effect_strength) for profile in unique_profiles]


def _generate_roster(*, size: int, seed: int) -> list[ExpertProfile]:
    rng = RNG(seed)
    names = [
        "Alex Grant",
        "Priya Desai",
        "Callum Price",
        "Beatrice Lowe",
        "Marcus Flint",
        "Serena Moore",
        "Hugo Bell",
        "Lila Chen",
        "Carmen Alvarez",
        "Ned Okoro",
        "Vera Singh",
        "Tom Hollins",
    ]
    specialties = [
        "ceramics",
        "silverware",
        "tools",
        "prints",
        "toys",
        "glassware",
        "clocks",
        "books",
    ]
    signature_styles = [
        "no-nonsense appraiser",
        "warm mentor",
        "methodical researcher",
        "risky gambler",
        "budget hawk",
        "story-first picker",
        "calm negotiator",
    ]
    moods = ["calm", "excitable", "methodical", "skeptical"]
    catchphrases = [
        "Let's not pay twice.",
        "I like the bones of this.",
        "Trust the patina.",
        "Let's make a cheeky offer.",
    ]

    profiles: list[ExpertProfile] = []
    for idx in range(size):
        name = names[idx % len(names)]
        specialty = specialties[idx % len(specialties)]
        style = signature_styles[idx % len(signature_styles)]
        profile = ExpertProfile(
            id=f"expert_{name.lower().replace(' ', '_')}",
            full_name=name,
            specialty=specialty,
            years_experience=8 + idx + rng.randint(0, 6),
            signature_style=style,
            appraisal_accuracy=round(0.72 + rng.uniform(0, 0.2), 2),
            negotiation_skill=round(0.55 + rng.uniform(-0.12, 0.25), 2),
            risk_appetite=round(0.35 + rng.uniform(-0.15, 0.4), 2),
            category_bias={specialty: round(1.05 + rng.uniform(0, 0.12), 2)},
            time_management=round(0.5 + rng.uniform(-0.15, 0.35), 2),
            trust_factor=round(0.5 + rng.uniform(-0.1, 0.25), 2),
            catchphrase=catchphrases[idx % len(catchphrases)],
            mood_baseline=rng.choice(moods),
        )
        profiles.append(profile)
    return profiles
