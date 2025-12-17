import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tests.simulation_utils import play_through_market


def test_teams_buy_three_items_and_keep_expert_budget():
    episode = play_through_market(seed=21, expert_min_budget=12.0)

    for team in episode.teams:
        assert team.team_item_count == episode.items_per_team
        assert team.budget_left >= 0.0
        assert team.budget_left >= episode.expert_min_budget
