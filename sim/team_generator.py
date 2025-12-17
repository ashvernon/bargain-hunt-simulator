from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from models.contestant import Contestant, ContestantProfile, RelationshipType
from sim.rng import RNG


@dataclass
class RelationshipTemplate:
    type: RelationshipType
    label: str
    description: str
    shared_surname: bool
    team_title: str


@dataclass
class TeamProfile:
    name: str
    relationship: str
    relationship_type: RelationshipType
    contestants: list[Contestant]


FIRST_NAMES = [
    "Amelia",
    "Arthur",
    "Beatrice",
    "Callum",
    "Chloe",
    "Declan",
    "Ella",
    "Ethan",
    "Freya",
    "George",
    "Harriet",
    "Imogen",
    "Isla",
    "Jacob",
    "Jasmine",
    "Kieran",
    "Layla",
    "Lewis",
    "Maya",
    "Naomi",
    "Noah",
    "Oliver",
    "Priya",
    "Rahul",
    "Rosie",
    "Sam",
    "Sophie",
    "Theo",
    "Toby",
    "Yasmin",
]

SURNAMES = [
    "Ahmed",
    "Bennett",
    "Campbell",
    "Davies",
    "Evans",
    "Fletcher",
    "Gallagher",
    "Hughes",
    "Jackson",
    "Jones",
    "Khan",
    "Marshall",
    "Morgan",
    "Patel",
    "Roberts",
    "Singh",
    "Smith",
    "Taylor",
    "Thompson",
    "Walker",
    "Wilson",
]

OCCUPATIONS = [
    "teacher",
    "nurse",
    "electrician",
    "youth worker",
    "graphic designer",
    "librarian",
    "civil servant",
    "history student",
    "shop owner",
    "paramedic",
    "retired postie",
    "engineer",
    "cafe manager",
    "museum guide",
    "office admin",
    "train driver",
]

HAIR_COLOURS = [
    ("brown", 0.38),
    ("blonde", 0.22),
    ("black", 0.20),
    ("grey", 0.12),
    ("red", 0.08),
]

MOODS = [
    ("buzzing", 0.2),
    ("focused", 0.2),
    ("quietly confident", 0.18),
    ("nervous", 0.14),
    ("excited", 0.16),
    ("cautiously optimistic", 0.12),
]

RELATIONSHIPS: list[RelationshipTemplate] = [
    RelationshipTemplate(RelationshipType.SIBLINGS, "Sisters", "sisters who binge car boot sales", True, "Siblings"),
    RelationshipTemplate(RelationshipType.SIBLINGS, "Brothers", "brothers raised on antiques fairs", True, "Brothers"),
    RelationshipTemplate(RelationshipType.FRIENDS, "Best mates", "best mates since uni", False, "Best Mates"),
    RelationshipTemplate(RelationshipType.COLLEAGUES, "Work pals", "colleagues from the office", False, "Workmates"),
    RelationshipTemplate(RelationshipType.COUPLE, "Married", "a married duo who love a bargain", False, "Married Duo"),
    RelationshipTemplate(RelationshipType.PARENT_CHILD, "Family team", "parent and grown-up child", True, "Family Pair"),
    RelationshipTemplate(RelationshipType.NEIGHBOURS, "Neighbours", "neighbours who swap antiques tips", False, "Neighbours"),
]


def weighted_choice(options: Iterable[tuple[str, float]], rng: RNG) -> str:
    total = sum(weight for _, weight in options)
    pick = rng.random() * total
    cumulative = 0.0
    last_item = None
    for item, weight in options:
        cumulative += weight
        last_item = item
        if pick <= cumulative:
            return item
    return last_item if last_item is not None else ""


def triangular_int(rng: RNG, low: int, high: int, mode: int) -> int:
    u = rng.random()
    c = (mode - low) / (high - low)
    if u < c:
        value = low + math.sqrt(u * (high - low) * (mode - low))
    else:
        value = high - math.sqrt((1 - u) * (high - low) * (high - mode))
    return int(round(value))


def clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _pick_relationships(rng: RNG, count: int) -> list[RelationshipTemplate]:
    pool = list(RELATIONSHIPS)
    rng.shuffle(pool)
    return pool[:count]


def _generate_profile_pair(rel: RelationshipTemplate, rng: RNG) -> list[ContestantProfile]:
    shared_surname = rng.choice(SURNAMES) if rel.shared_surname else None
    chosen_first = rng.choice(FIRST_NAMES)
    other_first = rng.choice([n for n in FIRST_NAMES if n != chosen_first])

    def build_profile(first_name: str, idx: int) -> ContestantProfile:
        surname = shared_surname or rng.choice(SURNAMES)
        age = triangular_int(rng, 20, 72, 46)
        hair_colour = weighted_choice(HAIR_COLOURS, rng)
        occupation = rng.choice(OCCUPATIONS)
        mood = weighted_choice(MOODS, rng)
        confidence = clamp(0.45 + rng.random() * 0.4)
        taste = clamp(0.5 + rng.random() * 0.35)
        profile_id = f"{rel.type.value}-{rng.randint(1000, 9999)}-{idx}"
        return ContestantProfile(
            id=profile_id,
            full_name=f"{first_name} {surname}",
            age=age,
            hair_colour=hair_colour,
            occupation=occupation,
            relationship_to_teammate=rel.description,
            relationship_type=rel.type,
            mood=mood,
            confidence=confidence,
            taste=taste,
        )

    return [build_profile(chosen_first, 1), build_profile(other_first, 2)]


def _assign_roles(rng: RNG) -> tuple[str, str]:
    role_sets = [
        ("Team Captain", "Spotter"),
        ("Strategist", "Dealer"),
        ("Buyer", "Researcher"),
    ]
    return rng.choice(role_sets)


def generate_random_teams(rng: RNG, *, count: int = 2, color_labels: list[str] | None = None) -> list[TeamProfile]:
    relationships = _pick_relationships(rng, count)
    teams: list[TeamProfile] = []
    for idx, rel in enumerate(relationships):
        profiles = _generate_profile_pair(rel, rng)
        roles = _assign_roles(rng)
        contestants: list[Contestant] = []
        for prof, role in zip(profiles, roles):
            contestants.append(prof.to_contestant(role=role))

        label = color_labels[idx] if color_labels and idx < len(color_labels) else "Team"
        team_name = f"{label} {rel.team_title}".strip()
        teams.append(
            TeamProfile(
                name=team_name,
                relationship=rel.description,
                relationship_type=rel.type,
                contestants=contestants,
            )
        )

    return teams
