from __future__ import annotations

import argparse
from pathlib import Path

from sim.balance_config import BalanceConfig
from sim.headless_balance_runner import run_headless, save_report


def parse_args():
    parser = argparse.ArgumentParser(description="Run headless balance simulation")
    parser.add_argument("--runs", type=int, default=2000, help="Number of episodes to run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--pricing-style", type=str, default="fair", choices=["fair", "overpriced", "chaotic"])
    parser.add_argument("--items-per-team", type=int, default=3)
    parser.add_argument("--config", type=Path, help="Optional JSON config path")
    parser.add_argument("--out", type=Path, default=Path("reports/balance_report.json"))
    parser.add_argument("--negotiate-chance", type=float, default=0.18)
    parser.add_argument("--negotiate-min", type=float, default=0.05)
    parser.add_argument("--negotiate-max", type=float, default=0.20)
    parser.add_argument("--csv", type=Path, help="Optional CSV output path with per-run metrics")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = BalanceConfig.from_json(args.config) if args.config else BalanceConfig()
    report = run_headless(
        runs=args.runs,
        seed=args.seed,
        pricing_style=args.pricing_style,
        items_per_team=args.items_per_team,
        negotiate_chance=args.negotiate_chance,
        negotiate_min=args.negotiate_min,
        negotiate_max=args.negotiate_max,
        cfg=cfg,
        csv_path=args.csv,
    )
    save_report(report, args.out)
    print(f"Saved report to {args.out}")
    if args.csv:
        print(f"Saved per-run CSV to {args.csv}")


if __name__ == "__main__":
    main()
