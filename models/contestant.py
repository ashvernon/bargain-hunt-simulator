from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RelationshipType(Enum):
    SIBLINGS = "siblings"
    FRIENDS = "friends"
    COLLEAGUES = "colleagues"
    COUPLE = "couple"
    PARENT_CHILD = "parent_child"
    NEIGHBOURS = "neighbours"


@dataclass
class ContestantProfile:
    id: str
    full_name: str
    age: int
    hair_colour: str
    occupation: str
    relationship_to_teammate: str
    relationship_type: RelationshipType
    mood: str
    confidence: float  # 0-1
    taste: float  # 0-1

    def first_name(self) -> str:
        return self.full_name.split(" ")[0]

    def to_contestant(self, role: str) -> "Contestant":
        return Contestant(
            name=self.first_name(),
            role=role,
            confidence=self.confidence,
            taste=self.taste,
            profile=self,
            full_name=self.full_name,
            age=self.age,
            hair_colour=self.hair_colour,
            occupation=self.occupation,
            relationship_to_teammate=self.relationship_to_teammate,
            mood=self.mood,
        )


@dataclass
class Contestant:
    name: str
    role: str
    confidence: float  # 0-1
    taste: float  # 0-1
    profile: Optional[ContestantProfile] = None
    full_name: Optional[str] = None
    age: Optional[int] = None
    hair_colour: Optional[str] = None
    occupation: Optional[str] = None
    relationship_to_teammate: Optional[str] = None
    mood: Optional[str] = None
