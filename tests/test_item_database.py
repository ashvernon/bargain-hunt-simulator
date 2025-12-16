import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sim.item_database import ItemDatabase


def test_load_jsonl_sets_image_and_attributes(tmp_path: Path):
    data_path = tmp_path / "items.jsonl"
    line = {
        "item_id": "it_test",
        "title": "Test Generated Item",
        "category": "decor",
        "era": "art-deco",
        "condition_score": 0.75,
        "rarity_score": 0.25,
        "true_value": 123.0,
        "image_filename": "assets/items/generated/it_test.png",
        "item_type": "vase",
        "year_hint": 1933,
        "materials": ["glass", "brass"],
    }
    data_path.write_text(f"{json.dumps(line)}\n", encoding="utf-8")

    db = ItemDatabase.load_jsonl(data_path)

    assert len(db.templates) == 1
    template = db.templates[0]
    assert template.image == "assets/items/generated/it_test.png"
    assert template.attributes["dataset_id"] == "it_test"
    assert template.attributes["materials"] == "glass, brass"

    item = template.instantiate(item_id=99)
    assert item.image_path == "assets/items/generated/it_test.png"
