import csv
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.auction_house import AuctionHouse
from models.auctioneer import Auctioneer
from sim.balance_config import BalanceConfig
from sim.headless_balance_runner import run_headless
from sim.rng import RNG


def test_headless_smoke_runs_and_has_reasonable_profit():
    cfg = BalanceConfig()
    report = run_headless(runs=120, seed=123, cfg=cfg)

    item_stats = report["profit"]["item"]
    team_stats = report["profit"]["team"]

    assert item_stats["count"] > 0
    assert team_stats["count"] > 0
    assert item_stats["mean"] < 300  # not absurdly high
    assert item_stats["p90"] < 800
    assert item_stats["pct_neg"] > 0  # some losses
    assert item_stats["pct_pos"] > 0.1


def test_auctioneer_and_house_respect_config():
    cfg = BalanceConfig()
    cfg.auctioneer.sigma_scale = 0.2
    cfg.auction_house.clamp_multiplier = 2.0

    rng = RNG(99)
    auctioneer = Auctioneer(name="Cfg", accuracy=cfg.auctioneer.default_accuracy)
    auction_house = AuctionHouse.generate(rng, cfg=cfg)
    report = run_headless(runs=40, seed=99, cfg=cfg, auctioneer=auctioneer, auction_house=auction_house)

    ratio = report["auction_ratio"]
    assert ratio["p90"] < 5.0  # clamp multiplier effect


def test_negotiation_config_can_raise_floor():
    cfg = BalanceConfig()
    cfg.negotiation.discount_min = 0.25
    cfg.negotiation.discount_max = 0.35

    report = run_headless(runs=60, seed=5, cfg=cfg, negotiate_chance=0.9)
    discounts = report["negotiation"]["discounts"]
    assert discounts["p10"] >= 0.15


def test_csv_report_is_written(tmp_path):
    cfg = BalanceConfig()
    csv_path = tmp_path / "runs.csv"
    report = run_headless(runs=5, seed=11, cfg=cfg, csv_path=csv_path)
    assert csv_path.exists()

    with csv_path.open() as f:
        rows = list(csv.reader(f))
    # header + rows for each team per episode
    assert rows[0][:4] == ["seed", "run_index", "mood", "gavel_awarded"]
    assert len(rows) == 1 + 5 * 2  # two teams per run by default
    assert report["profit"]["team"]["count"] > 0
