import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from game_state import GameState


def test_toggle_speed_progression_from_default():
    state = GameState.__new__(GameState)
    state.time_scale = 1.0
    state.episode = SimpleNamespace(time_scale=1.0)

    for expected in (2.0, 10.0, 20.0, 2.0):
        state._toggle_speed()
        assert state.time_scale == expected
        assert state.episode.time_scale == expected
