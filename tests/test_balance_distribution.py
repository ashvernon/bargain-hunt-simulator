import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sim.balance_config import BalanceConfig
from sim.headless_balance_runner import run_headless


@pytest.mark.slow
def test_distribution_stability_across_seeds():
    cfg = BalanceConfig()
    report_a = run_headless(runs=200, seed=1, cfg=cfg)
    report_b = run_headless(runs=200, seed=2, cfg=cfg)

    mean_a = report_a["profit"]["team"]["mean"]
    mean_b = report_b["profit"]["team"]["mean"]
    assert abs(mean_a - mean_b) < 120


@pytest.mark.slow
def test_gavel_award_is_not_degenerate():
    cfg = BalanceConfig()
    cfg.gavel.probability = 0.5
    cfg.gavel.profit_threshold = 50.0

    report = run_headless(runs=300, seed=7, cfg=cfg)
    assert 0.05 < report["gavel"]["rate"] < 0.95
