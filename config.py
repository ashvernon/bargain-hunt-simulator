from dataclasses import dataclass

@dataclass(frozen=True)
class GameConfig:
    # Window
    window_w: int = 1100
    window_h: int = 700
    fps: int = 60

    # Market phase
    market_seconds: float = 35.0
    team_speed_px_s: float = 160.0
    buy_radius_px: float = 28.0

    # Show rules
    items_per_team: int = 3          # team purchases
    expert_extra_item: int = 1       # expert leftover purchase (0/1)
    starting_budget: float = 300.0

    # Visual layout
    hud_w: int = 360
    margin: int = 18
