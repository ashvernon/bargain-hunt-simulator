from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Iterable, Sequence


def _percentile(sorted_vals: Sequence[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(pct * (len(sorted_vals) - 1))
    return sorted_vals[idx]


def summarize_distribution(vals: Iterable[float]) -> dict:
    data = sorted(vals)
    if not data:
        return {
            "count": 0,
            "mean": 0.0,
            "std_est": 0.0,
            "median": 0.0,
            "pct_pos": 0.0,
            "pct_neg": 0.0,
            "p10": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p90": 0.0,
        }
    mu = mean(data)
    var = mean((x - mu) ** 2 for x in data)
    std = var**0.5
    pos = sum(1 for v in data if v > 0)
    neg = sum(1 for v in data if v < 0)
    return {
        "count": len(data),
        "mean": mu,
        "std_est": std,
        "median": _percentile(data, 0.5),
        "pct_pos": pos / len(data),
        "pct_neg": neg / len(data),
        "p10": _percentile(data, 0.10),
        "p25": _percentile(data, 0.25),
        "p50": _percentile(data, 0.50),
        "p75": _percentile(data, 0.75),
        "p90": _percentile(data, 0.90),
    }


def episodes_to_rows(episodes, *, seed: int) -> list[list]:
    """Flatten episode results to CSV rows.

    Each row corresponds to a team within an episode to make per-run analysis
    easy in spreadsheets or notebooks.
    """
    rows: list[list] = []
    headers = [
        "seed",
        "run_index",
        "mood",
        "gavel_awarded",
        "team_name",
        "spent_total",
        "sold_total",
        "profit_total",
        "roi",
        "best_lot_name",
        "best_lot_profit",
    ]
    for idx, ep in enumerate(episodes):
        for tr in ep.team_results:
            best_name = tr.best_lot.name if tr.best_lot else ""
            best_profit = tr.best_lot.profit if tr.best_lot else 0.0
            rows.append(
                [
                    seed,
                    idx,
                    ep.mood,
                    ep.gavel_awarded,
                    tr.team_name,
                    tr.spent_total,
                    tr.sold_total,
                    tr.profit_total,
                    tr.roi,
                    best_name,
                    best_profit,
                ]
            )
    return [headers] + rows


@dataclass
class GavelMetrics:
    awards: int = 0
    eligible: int = 0

    def rate(self) -> float:
        return (self.awards / self.eligible) if self.eligible else 0.0

    def to_dict(self):
        data = asdict(self)
        data["rate"] = self.rate()
        return data
