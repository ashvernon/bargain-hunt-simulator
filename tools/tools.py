from __future__ import annotations

import csv
import json
import os
import random
import string
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple

# -----------------------------
# Config: tweak these
# -----------------------------
DEFAULT_STYLE_CLAUSE = (
    "flat cartoon illustration, BBC daytime TV graphics style circa early 2000s, "
    "clean outlines, soft shading, muted warm colour palette, friendly and readable, "
    "no realism, no photorealism, simple shapes, suitable for a 2D game, isolated object, "
    "transparent background, no text, no watermark"
)

CATEGORIES = {
    "ceramics": ["vase", "bowl", "figurine", "plate", "teapot"],
    "clocks": ["mantel clock", "wall clock", "pocket watch", "carriage clock"],
    "tools": ["brass compass", "hand plane", "antique hammer", "oil can", "measuring calipers"],
    "decor": ["candelabra", "mirror", "picture frame", "table lamp", "ornament"],
    "glassware": ["decanter", "wine glass set", "perfume bottle", "amber vase"],
    "textiles": ["embroidered scarf", "lace table runner", "tapestry fragment", "silk handkerchief"],
    "toys": ["tin robot", "wind-up toy", "wooden train", "doll"],
    "furniture": ["stool", "side table", "wall shelf", "small cabinet handle set"],
    "art": ["oil portrait", "landscape painting", "etching print", "poster"],
    "books": ["leather-bound book", "antique journal", "map folio", "sheet music booklet"],
}

ERAS = [
    ("Georgian", 1714, 1830),
    ("Victorian", 1837, 1901),
    ("Edwardian", 1901, 1910),
    ("Art Deco", 1920, 1939),
    ("Mid-century", 1945, 1969),
    ("Retro 70s", 1970, 1979),
    ("Vintage 80s", 1980, 1989),
]

MATERIALS_BY_CATEGORY = {
    "ceramics": ["porcelain", "earthenware", "stoneware", "glazed ceramic"],
    "clocks": ["brass", "wood", "bakelite", "glass"],
    "tools": ["iron", "steel", "brass", "wood"],
    "decor": ["brass", "wood", "glass", "ceramic"],
    "glassware": ["glass", "crystal", "amber glass"],
    "textiles": ["cotton", "silk", "linen", "lace"],
    "toys": ["tin", "wood", "plastic", "cloth"],
    "furniture": ["wood", "iron", "brass"],
    "art": ["canvas", "paper", "wood frame"],
    "books": ["paper", "leather", "cloth cover"],
}

# A simple “rarity weight” per category for variety in values
CATEGORY_VALUE_MULT = {
    "ceramics": 1.0,
    "clocks": 1.25,
    "tools": 0.9,
    "decor": 1.05,
    "glassware": 1.1,
    "textiles": 0.85,
    "toys": 1.0,
    "furniture": 1.15,
    "art": 1.3,
    "books": 0.8,
}

# -----------------------------
# Data model
# -----------------------------
@dataclass
class FakeItem:
    item_id: str
    title: str
    category: str
    item_type: str
    era: str
    year_hint: int
    materials: List[str]
    condition_score: float
    rarity_score: float
    true_value: int
    prompt_image: str
    image_filename: str


# -----------------------------
# Helpers
# -----------------------------
def _id(prefix: str = "it") -> str:
    tail = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{tail}"

def _pick_era() -> Tuple[str, int]:
    era, y0, y1 = random.choice(ERAS)
    return era, random.randint(y0, y1)

def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _roll_condition() -> float:
    # Bias toward “decent” condition with some bad luck
    x = random.gauss(mu=0.72, sigma=0.18)
    return round(_clamp01(x), 2)

def _roll_rarity() -> float:
    # Most items common; a few rare
    # Skew using squared uniform
    x = random.random() ** 2
    return round(_clamp01(x), 2)

def _estimate_true_value(category: str, era: str, year_hint: int, condition: float, rarity: float) -> int:
    # Baseline
    base = random.uniform(15, 120)

    # Era bump (older tends to be more valuable, but not always)
    era_mult = {
        "Georgian": 1.35,
        "Victorian": 1.25,
        "Edwardian": 1.15,
        "Art Deco": 1.30,
        "Mid-century": 1.10,
        "Retro 70s": 0.95,
        "Vintage 80s": 0.9,
    }.get(era, 1.0)

    cat_mult = CATEGORY_VALUE_MULT.get(category, 1.0)

    # Condition & rarity influence
    cond_mult = 0.55 + 0.75 * condition         # 0.55..1.30
    rarity_mult = 0.85 + 1.5 * rarity            # 0.85..2.35

    # Small randomness for show drama
    noise = random.lognormvariate(mu=0.0, sigma=0.28)

    value = base * era_mult * cat_mult * cond_mult * rarity_mult * noise

    # Keep within a sane “Bargain Hunt-ish” range
    return int(max(5, min(1200, round(value))))

def _condition_descriptor(condition: float) -> str:
    if condition >= 0.85:
        return "excellent condition"
    if condition >= 0.70:
        return "good condition with minor wear"
    if condition >= 0.50:
        return "fair condition with visible wear"
    return "poor condition, noticeable damage and wear"

def _rarity_descriptor(rarity: float) -> str:
    if rarity >= 0.75:
        return "rare"
    if rarity >= 0.45:
        return "uncommon"
    return "common"

def _make_title(era: str, materials: List[str], item_type: str) -> str:
    mat = materials[0].title()
    # e.g. "Victorian Brass Mantel Clock"
    return f"{era} {mat} {item_type.title()}"

def _make_image_prompt(title: str, item_type: str, era: str, materials: List[str],
                       condition: float, rarity: float, style_clause: str) -> str:
    cond_desc = _condition_descriptor(condition)
    rar_desc = _rarity_descriptor(rarity)
    mats = ", ".join(materials[:2])

    return (
        f"{style_clause}. "
        f"Subject: a single {rar_desc} {era.lower()} {item_type} made of {mats}. "
        f"Design: simple readable silhouette, slightly exaggerated features, charming imperfections. "
        f"Condition: {cond_desc}. "
        f"Framing: centered, no background scene, no props, no people."
    )

# -----------------------------
# Generator
# -----------------------------
def generate_items(
    n: int = 100,
    seed: int = 123,
    style_clause: str = DEFAULT_STYLE_CLAUSE,
    out_dir: str = "data",
    image_dir_hint: str = "assets/items/generated"
) -> List[FakeItem]:
    random.seed(seed)

    items: List[FakeItem] = []

    # Flatten category -> types with weights if you want (optional)
    category_list = list(CATEGORIES.keys())

    for _ in range(n):
        category = random.choice(category_list)
        item_type = random.choice(CATEGORIES[category])

        era, year_hint = _pick_era()
        condition = _roll_condition()
        rarity = _roll_rarity()

        materials_pool = MATERIALS_BY_CATEGORY.get(category, ["mixed materials"])
        materials = random.sample(materials_pool, k=min(2, len(materials_pool)))

        title = _make_title(era, materials, item_type)
        true_value = _estimate_true_value(category, era, year_hint, condition, rarity)

        item_id = _id()
        image_filename = f"{item_id}.png"  # you create and save it here later
        prompt = _make_image_prompt(title, item_type, era, materials, condition, rarity, style_clause)

        items.append(FakeItem(
            item_id=item_id,
            title=title,
            category=category,
            item_type=item_type,
            era=era,
            year_hint=year_hint,
            materials=materials,
            condition_score=condition,
            rarity_score=rarity,
            true_value=true_value,
            prompt_image=prompt,
            image_filename=os.path.join(image_dir_hint, image_filename).replace("\\", "/"),
        ))

    # Write outputs
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    jsonl_path = Path(out_dir) / f"items_{n}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(asdict(it), ensure_ascii=False) + "\n")

    csv_path = Path(out_dir) / f"items_{n}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(items[0]).keys()))
        writer.writeheader()
        for it in items:
            writer.writerow(asdict(it))

    print(f"Wrote: {jsonl_path}")
    print(f"Wrote: {csv_path}")
    print(f"Image filename hint folder: {image_dir_hint}")

    return items

if __name__ == "__main__":
    generate_items(n=100, seed=123)
