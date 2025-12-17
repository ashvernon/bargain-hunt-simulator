import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ai.spend_plan import SpendPlan, SpendPlanName
from models.episode import Episode
from models.item import Item
from models.market import Market
from models.stall import Stall


def play_through_market(
    seed: int,
    *,
    expert_min_budget: float = 1.0,
    steps: int = 500,
    team_speed: float = 420.0,
    buy_radius: float = 280.0,
) -> Episode:
    episode = Episode(
        ep_idx=0,
        seed=seed,
        play_rect=(0, 0, 1280, 720),
        items_per_team=3,
        starting_budget=400.0,
        expert_min_budget=expert_min_budget,
    )
    episode.setup()
    generous_plan = SpendPlan(SpendPlanName.THREE_SMALL, price_caps=(1.0, 1.0, 1.0))
    for team in episode.teams:
        team.spend_plan = generous_plan

    episode.market = _build_affordable_market()

    for _ in range(steps):
        episode.update_market_ai(dt=0.35, team_speed=team_speed, buy_radius=buy_radius)
        if all(not team.can_buy_more(episode.items_per_team) for team in episode.teams):
            break

    return episode


def run_episode_to_results(seed: int, *, expert_min_budget: float = 1.0) -> Episode:
    episode = play_through_market(seed, expert_min_budget=expert_min_budget)

    assert all(team.team_item_count == episode.items_per_team for team in episode.teams)

    episode.reserve_expert_budget()
    episode.prepare_expert_picks()
    for team in episode.teams:
        include = team.expert_pick_item is not None
        episode.mark_expert_choice(team, include=include)

    episode.start_appraisal()
    episode.start_team_auction()
    while not episode.auction_done:
        episode.step_auction()

    episode.start_expert_auction()
    while not episode.auction_done:
        episode.step_auction()

    episode.compute_results()
    return episode


def _build_affordable_market() -> Market:
    stalls: list[Stall] = []
    base_id = 1
    layout = [(160, 260), (520, 360), (900, 300)]
    price_sets = [
        [25.0, 32.0, 18.0, 22.0],
        [28.0, 34.0, 26.0],
        [24.0, 27.0, 29.0],
    ]

    for idx, (pos, prices) in enumerate(zip(layout, price_sets), start=1):
        items = []
        for offset, price in enumerate(prices):
            items.append(
                Item(
                    item_id=base_id + offset,
                    name=f"Test Item {base_id + offset}",
                    category="tools",
                    era="modern",
                    condition=0.7,
                    rarity=0.3,
                    style_score=0.6,
                    true_value=120.0,
                    shop_price=price,
                )
            )
        stalls.append(
            Stall(
                stall_id=idx,
                name=f"Budget Stall {idx}",
                rect=(pos[0], pos[1], 120, 80),
                pricing_style="fair",
                discount_chance=0.0,
                discount_min=0.0,
                discount_max=0.0,
                items=items,
            )
        )
        base_id += len(items)

    return Market(stalls=stalls, _next_item_id=base_id)
