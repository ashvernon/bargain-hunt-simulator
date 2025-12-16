import argparse

from ui.pygame_app import run_app


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Bargain Hunt simulator")
    parser.add_argument("--seed", type=int, default=123, help="Random seed for deterministic runs")
    parser.add_argument("--episode", type=int, default=1, help="Episode index")
    parser.add_argument(
        "--market-minutes",
        type=float,
        default=60.0,
        help="Length of the market phase in minutes (default: 60)",
    )
    parser.add_argument(
        "--market-seconds",
        type=float,
        default=None,
        help="Override market duration directly in seconds",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    market_seconds = args.market_seconds if args.market_seconds is not None else args.market_minutes * 60
    run_app(seed=args.seed, episode_idx=args.episode, market_seconds=market_seconds)
