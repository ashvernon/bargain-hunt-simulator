import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.simulation_utils import run_episode_to_results


def snapshot_episode(seed: int):
    episode = run_episode_to_results(seed, expert_min_budget=10.0)
    return {
        "winner": episode.winner.name,
        "teams": [
            {
                "name": team.name,
                "spend": team.spend,
                "revenue": team.revenue,
                "profit": team.profit,
                "golden_gavel": team.golden_gavel,
                "items": [
                    (it.name, it.shop_price, it.auction_price, it.is_expert_pick)
                    for it in team.included_items
                ],
            }
            for team in episode.teams
        ],
    }


def test_episode_flow_is_deterministic_with_seed():
    first = snapshot_episode(seed=99)
    second = snapshot_episode(seed=99)
    assert first == second
