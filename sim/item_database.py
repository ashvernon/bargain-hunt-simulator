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
    def load_jsonl(cls, path: Path) -> "ItemDatabase":
        """Load item templates from a JSONL file.

        Each line is expected to be a JSON object containing at least:
        - title (used for the item name)
        - category
        - era
        - condition_score, rarity_score, true_value
        - image_filename (relative path to the generated asset)
        """

        if not path.exists():
            return cls([])

        templates: list[ItemTemplate] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)

                name = entry.get("title") or entry.get("name") or "Unknown item"
                condition = float(entry.get("condition_score", 0.6))
                rarity = float(entry.get("rarity_score", 0.5))
                style_score = float(entry.get("style_score", rarity))
                true_value = float(entry.get("true_value", 50.0))

                attributes: dict[str, str] = {}
                if "item_id" in entry:
                    attributes["dataset_id"] = str(entry["item_id"])
                if "item_type" in entry:
                    attributes["item_type"] = str(entry["item_type"])
                if "year_hint" in entry:
                    attributes["year_hint"] = str(entry["year_hint"])
                if "materials" in entry:
                    attributes["materials"] = ", ".join(map(str, entry.get("materials", [])))

                templates.append(
                    ItemTemplate(
                        name=name,
                        category=str(entry.get("category", "misc")),
                        era=str(entry.get("era", "unknown")),
                        condition=condition,
                        rarity=rarity,
                        style_score=style_score,
                        true_value=true_value,
                        description=entry.get("description", entry.get("prompt_image", "")),
                        image=entry.get("image_filename"),
                        attributes=attributes,
                    )
                )

        return cls(templates)

    @classmethod
    def load_default(cls) -> "ItemDatabase":
        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        return cls.load(assets_dir / "items.json")

    @classmethod
    def load_generated(cls) -> "ItemDatabase":
        data_dir = Path(__file__).resolve().parent.parent / "data"
        return cls.load_jsonl(data_dir / "items_100.jsonl")

    @classmethod
    def load_combined(cls) -> "ItemDatabase":
        default_templates = cls.load_default().templates
        generated_templates = cls.load_generated().templates
        return cls(default_templates + generated_templates)

    def pick_template(self, rng) -> ItemTemplate | None:
        if not self.templates:
            return None
        return rng.choice(self.templates)

    def next_item(self, rng, item_id: int) -> Item:
        template = self.pick_template(rng)
        if template:
            return template.instantiate(item_id)
        raise ValueError("ItemDatabase is empty; cannot generate item")
