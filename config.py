from dataclasses import dataclass

@dataclass(frozen=True)
class GameConfig:
    # Window
    window_w: int = 1100
    window_h: int = 700
    fps: int = 60
    show_splash_video: bool = True
    splash_video_max_seconds: float = 8.0
    splash_video_path: str = "assets/video/into_vid.mp4"
    show_host_intro: bool = True

    # Market phase
    # Default to an hour-long shopping period
    market_seconds: float = 60.0 * 60.0
    team_speed_px_s: float = 160.0
    buy_radius_px: float = 28.0
    buy_decision_seconds_range: tuple[float, float] = (6.0, 12.0)
    expert_chat_probability: float = 0.2
    expert_chat_seconds_range: tuple[float, float] = (8.0, 18.0)
    backtrack_probability: float = 0.22
    market_pace_multiplier: float = 0.55

    # Experts
    expert_roster_path: str = "data/experts.json"
    expert_roster_size: int = 10
    expert_effect_strength: float = 1.0
    expert_regen_allowed: bool = False
    expert_force_regen: bool = False

    # Item sourcing
    # Which dataset to use for generating items: default assets JSON, generated
    # JSONL set, or a combination of both. Defaults to the generated JSONL set
    # so item images and metadata from data/items_100.jsonl are available in-game.
    item_source: str = "generated"

    # Show rules
    items_per_team: int = 3          # team purchases
    expert_extra_item: int = 1       # expert leftover purchase (0/1)
    starting_budget: float = 300.0
    expert_min_budget: float = 1.0   # must be reserved for the expert bonus buy

    # Visual layout
    hud_w: int = 360
    margin: int = 18
