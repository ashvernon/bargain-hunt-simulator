import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sim.rng import RNG
from sim.team_generator import generate_random_teams


def test_generate_random_teams_is_deterministic():
    teams_first = generate_random_teams(RNG(2024))
    teams_second = generate_random_teams(RNG(2024))

    assert [t.name for t in teams_first] == [t.name for t in teams_second]
    assert [
        [(c.full_name, c.mood, c.relationship_to_teammate) for c in t.contestants]
        for t in teams_first
    ] == [
        [(c.full_name, c.mood, c.relationship_to_teammate) for c in t.contestants]
        for t in teams_second
    ]


def test_generated_contestants_have_required_fields():
    teams = generate_random_teams(RNG(19))

    for team in teams:
        assert len(team.contestants) == 2
        assert team.relationship
        for contestant in team.contestants:
            assert contestant.full_name
            assert contestant.age is not None
            assert contestant.hair_colour
            assert contestant.occupation
            assert contestant.relationship_to_teammate
            assert contestant.mood
            assert contestant.profile is not None
            assert contestant.profile.relationship_type == team.relationship_type
