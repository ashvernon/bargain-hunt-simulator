from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from models.item import Item


@dataclass
class ItemTemplate:
    name: str
    category: str
    era: str
    condition: float
    rarity: float
    style_score: float
    true_value: float
    description: str = ""
    image: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)

    def instantiate(self, item_id: int) -> Item:
        return Item(
            item_id=item_id,
            name=self.name,
            category=self.category,
            era=self.era,
            condition=self.condition,
            rarity=self.rarity,
            style_score=self.style_score,
            true_value=self.true_value,
            shop_price=0.0,
            description=self.description,
            image_path=self.image,
            attributes=dict(self.attributes),
        )


class ItemDatabase:
    def __init__(self, templates: Iterable[ItemTemplate]):
        self.templates = list(templates)

    @classmethod
    def load(cls, path: Path) -> "ItemDatabase":
        if not path.exists():
            return cls([])

        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        templates = []
        for entry in raw:
            templates.append(
                ItemTemplate(
                    name=entry["name"],
                    category=entry["category"],
                    era=entry["era"],
                    condition=float(entry.get("condition", 0.6)),
                    rarity=float(entry.get("rarity", 0.5)),
                    style_score=float(entry.get("style_score", 0.5)),
                    true_value=float(entry.get("true_value", 50.0)),
                    description=entry.get("description", ""),
                    image=entry.get("image"),
                    attributes=entry.get("attributes", {}),
                )
            )

        return cls(templates)

    @classmethod
    def load_default(cls) -> "ItemDatabase":
        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        return cls.load(assets_dir / "items.json")

    def pick_template(self, rng) -> ItemTemplate | None:
        if not self.templates:
            return None
        return rng.choice(self.templates)

    def next_item(self, rng, item_id: int) -> Item:
        template = self.pick_template(rng)
        if template:
            return template.instantiate(item_id)
        raise ValueError("ItemDatabase is empty; cannot generate item")
