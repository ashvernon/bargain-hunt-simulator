import os

import pygame

from config import GameConfig
from tests.simulation_utils import play_through_market
from ui.screens.auction_screen import AuctionScreen


def _prepare_episode(seed: int):
    episode = play_through_market(seed, expert_min_budget=10.0)
    episode.reserve_expert_budget()
    episode.prepare_expert_picks()
    for team in episode.teams:
        include = team.expert_pick_item is not None
        episode.mark_expert_choice(team, include=include)
    episode.start_appraisal()
    return episode


def _collect_headless_sales(seed: int):
    episode = _prepare_episode(seed)
    sequences = {}

    for start_fn, stage_name in ((episode.start_team_auction, "team"), (episode.start_expert_auction, "expert")):
        start_fn()
        sales = []
        while not episode.auction_done:
            lot = episode.auction_queue[episode.auction_cursor]
            price = episode.auction_house.sell(lot.item, episode.rng)
            sales.append((lot.item.name, price))
            episode.finalize_auction_sale(lot, price)
        sequences[stage_name] = sales

    return sequences


def _collect_screen_sales(seed: int):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()

    episode = _prepare_episode(seed)
    screen = AuctionScreen(GameConfig(), episode)
    sequences = {}

    for start_fn, stage_name in ((episode.start_team_auction, "team"), (episode.start_expert_auction, "expert")):
        screen.reset_for_new_queue()
        start_fn()

        sales = []
        last_recorded = None
        guard = 0

        while not episode.auction_done:
            before = episode.last_sold
            screen.update(0.5)

            if episode.last_sold is not None and episode.last_sold is not before and episode.last_sold is not last_recorded:
                lot = episode.last_sold
                sales.append((lot.item.name, lot.item.auction_price))
                last_recorded = episode.last_sold

            guard += 1
            assert guard < 2000, "auction screen simulation did not finish"

        sequences[stage_name] = sales

    pygame.quit()
    return sequences


def test_auction_screen_visual_rng_does_not_shift_sales():
    headless = _collect_headless_sales(seed=77)
    screen = _collect_screen_sales(seed=77)
    assert headless == screen
