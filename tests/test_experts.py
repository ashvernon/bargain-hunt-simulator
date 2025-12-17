import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import GameConfig
from models.episode import Episode
from sim.expert_roster import assign_episode_experts, load_expert_roster
from sim.rng import RNG


def test_expert_roster_loads_10():
    cfg = GameConfig()
    roster = load_expert_roster(cfg.expert_roster_path, cfg.expert_roster_size)

    assert len(roster) == cfg.expert_roster_size
    assert roster[0].id == "expert_alex_grant"
    assert roster[0].full_name == "Alex Grant"


def test_experts_persist_across_assignments():
    cfg = GameConfig()
    roster = load_expert_roster(cfg.expert_roster_path, cfg.expert_roster_size)

    first_draw = assign_episode_experts(RNG(99), roster, effect_strength=cfg.expert_effect_strength)
    second_draw = assign_episode_experts(RNG(99), roster, effect_strength=cfg.expert_effect_strength)

    assert [exp.profile.id for exp in first_draw] == [exp.profile.id for exp in second_draw]


def test_expert_assignment_distinct_per_episode():
    cfg = GameConfig()
    episode = Episode(0, seed=5, play_rect=(0, 0, 0, 0), items_per_team=3, starting_budget=50, cfg=cfg)
    episode.setup()

    assigned_ids = {team.expert.profile.id for team in episode.teams}

    assert len(assigned_ids) == 2
