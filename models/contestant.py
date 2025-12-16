from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Contestant:
    name: str
    role: str
    confidence: float  # 0-1
    taste: float  # 0-1
