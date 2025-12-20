from __future__ import annotations
from dataclasses import dataclass

from models.item import Item
from sim.item_database import ItemDatabase

CATEGORIES = ["ceramics", "clocks", "tools", "glassware", "prints", "toys", "silverware", "books"]
ERAS = ["victorian", "edwardian", "mid-century", "70s", "modern", "art-deco"]


from sim.balance_config import BalanceConfig


def _generate_fallback_item(rng, item_id: int, cfg: BalanceConfig | None = None) -> Item:
    """Generate a synthetic item if the item database is empty."""
    cfg = cfg or BalanceConfig()
    cat = rng.choice(CATEGORIES)
    era = rng.choice(ERAS)

    condition = max(0.25, min(1.0, rng.uniform(0.35, 1.0)))
    rarity = max(0.05, min(1.0, rng.uniform(0.1, 1.0)))
    style = max(0.05, min(1.0, rng.uniform(0.1, 1.0)))

    # "True value" is latent, slightly heavy-tailed to allow occasional gems
    base = 20 + 180 * (0.55 * rarity + 0.45 * style)
    true_value = base * (0.55 + 0.75 * condition) * rng.lognormal(0.0, cfg.true_value.fallback_sigma)
    true_value = float(round(true_value, 2))

    return Item(
        item_id=item_id,
        name=f"{era} {cat[:-1] if cat.endswith('s') else cat} #{item_id}",
        category=cat,
        era=era,
        condition=condition,
        rarity=rarity,
        style_score=style,
        true_value=true_value,
        shop_price=0.0,
    )


@dataclass
class ItemFactory:
    database: ItemDatabase

    @classmethod
    def with_default_db(cls) -> "ItemFactory":
        return cls(ItemDatabase.load_default())

    @classmethod
    def from_source(cls, source: str) -> "ItemFactory":
        source = source.lower()
        if source in {"default", "assets"}:
            db = ItemDatabase.load_default()
        elif source == "generated":
            db = ItemDatabase.load_generated()
        elif source == "combined":
            db = ItemDatabase.load_combined()
        else:
            raise ValueError(f"Unknown item source '{source}'")
        return cls(db)

    def make_item(self, rng, item_id: int, cfg: BalanceConfig | None = None) -> Item:
        if self.database.templates:
            return self.database.next_item(rng, item_id)
        return _generate_fallback_item(rng, item_id, cfg)


def make_item(rng, item_id: int, cfg: BalanceConfig | None = None) -> Item:
    """Convenience wrapper to avoid plumbing ItemFactory everywhere."""
    if not hasattr(make_item, "_factory"):
        make_item._factory = ItemFactory.with_default_db()
    factory: ItemFactory = make_item._factory
    return factory.make_item(rng, item_id, cfg)


def configure_item_factory(source: str):
    """Set the global ItemFactory used by make_item.

    This should be called during application startup to ensure the correct
    dataset is used when generating items.
    """

    make_item._factory = ItemFactory.from_source(source)
