from __future__ import annotations
from dataclasses import dataclass
from models.item import Item

CATEGORIES = ["ceramics", "clocks", "tools", "glassware", "prints", "toys", "silverware", "books"]
ERAS = ["victorian", "edwardian", "mid-century", "70s", "modern", "art-deco"]

def make_item(rng, item_id: int) -> Item:
    cat = rng.choice(CATEGORIES)
    era = rng.choice(ERAS)

    condition = max(0.25, min(1.0, rng.uniform(0.35, 1.0)))
    rarity = max(0.05, min(1.0, rng.uniform(0.1, 1.0)))
    style = max(0.05, min(1.0, rng.uniform(0.1, 1.0)))

    # "True value" is latent, slightly heavy-tailed to allow occasional gems
    base = 20 + 180 * (0.55 * rarity + 0.45 * style)
    true_value = base * (0.55 + 0.75 * condition) * rng.lognormal(0.0, 0.35)
    true_value = float(round(true_value, 2))

    # Shop price: depends on stall pricing style; set later via pricing module
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
