from dataclasses import dataclass

@dataclass(frozen=True)
class GameConfig:
    # Window
    window_w: int = 1100
    window_h: int = 700
    fps: int = 60
    show_splash: bool = True
    splash_duration: float = 8.0
    splash_video_path: str = "assets/video/into_vid.mp4"

    # Market phase
    # Default to an hour-long shopping period
    market_seconds: float = 60.0 * 60.0
    team_speed_px_s: float = 160.0
    buy_radius_px: float = 28.0

    # Item sourcing
    # Which dataset to use for generating items: default assets JSON, generated
    # JSONL set, or a combination of both
    item_source: str = "default"

    # Show rules
    items_per_team: int = 3          # team purchases
    expert_extra_item: int = 1       # expert leftover purchase (0/1)
    starting_budget: float = 300.0

    # Visual layout
    hud_w: int = 360
    margin: int = 18
