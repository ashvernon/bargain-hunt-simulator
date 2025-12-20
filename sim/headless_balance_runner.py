from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

from models.auction_house import AuctionHouse
from models.auction_result import AuctionRoundResult
from models.auctioneer import Auctioneer
from models.item import Item
from models.team import Team
from sim.balance_config import BalanceConfig
from sim.balance_metrics import GavelMetrics, episodes_to_rows, summarize_distribution
from sim.item_factory import ItemFactory
from sim.pricing import negotiate, set_shop_price
from sim.rng import RNG


@dataclass
class EpisodeResult:
    team_results: list[AuctionRoundResult]
    gavel_awarded: bool
    mood: str
    negotiation_discounts: list[float]
    negotiation_successes: int
    negotiation_total: int

    def to_dict(self):
        return {
            "team_results": [asdict(tr) for tr in self.team_results],
            "gavel_awarded": self.gavel_awarded,
            "mood": self.mood,
            "negotiation_discounts": self.negotiation_discounts,
            "negotiation_successes": self.negotiation_successes,
            "negotiation_total": self.negotiation_total,
        }


def _maybe_award_gavel(team_results: Iterable[AuctionRoundResult], rng, cfg: BalanceConfig) -> bool:
    best = max(team_results, key=lambda r: r.best_lot.profit if r.best_lot else float("-inf"))
    if not best.best_lot:
        return False
    threshold = cfg.gavel.profit_threshold
    if best.best_lot.profit < threshold:
        return False
    return rng.random() < cfg.gavel.probability


def run_episode(
    rng: RNG,
    *,
    runs_per_team: int = 3,
    pricing_style: str = "fair",
    negotiate_chance: float = 0.18,
    negotiate_min: float = 0.05,
    negotiate_max: float = 0.20,
    teams: list[Team],
    factory: ItemFactory,
    auctioneer: Auctioneer,
    auction_house: AuctionHouse,
    cfg: BalanceConfig,
) -> EpisodeResult:
    results: list[AuctionRoundResult] = []
    discounts: list[float] = []
    neg_successes = 0
    neg_total = 0
    item_id = 1
    for team in teams:
        items: list[Item] = []
        for _ in range(runs_per_team):
            item = factory.make_item(rng, item_id)
            item_id += 1
            set_shop_price(item, rng, pricing_style, cfg=cfg)
            did, disc = negotiate(
                item,
                rng,
                negotiate_chance,
                negotiate_min,
                negotiate_max,
                expert_bonus=team.negotiation_bonus(team.expert.negotiation_bonus)
                if hasattr(team, "expert") and hasattr(team, "negotiation_bonus")
                else 0.0,
                cfg=cfg,
            )
            item.was_negotiated = did
            if did:
                neg_successes += 1
                discounts.append(disc)
            neg_total += 1
            item.appraised_value = auctioneer.appraise(item, rng, cfg=cfg)
            item.auction_price = auction_house.sell(item, rng, cfg=cfg)
            items.append(item)
        results.append(AuctionRoundResult.from_team(team, items))
    gavel_awarded = _maybe_award_gavel(results, rng, cfg)
    return EpisodeResult(
        team_results=results,
        gavel_awarded=gavel_awarded,
        mood=auction_house.mood,
        negotiation_discounts=discounts,
        negotiation_successes=neg_successes,
        negotiation_total=neg_total,
    )


def run_headless(
    *,
    runs: int = 100,
    seed: int = 42,
    pricing_style: str = "fair",
    items_per_team: int = 3,
    negotiate_chance: float = 0.18,
    negotiate_min: float = 0.05,
    negotiate_max: float = 0.20,
    cfg: BalanceConfig | None = None,
    team_factory=None,
    item_factory: ItemFactory | None = None,
    auctioneer: Auctioneer | None = None,
    auction_house: AuctionHouse | None = None,
    csv_path: str | Path | None = None,
) -> dict:
    cfg = cfg or BalanceConfig()
    rng = RNG(seed)
    factory = item_factory or ItemFactory.with_default_db()
    auctioneer = auctioneer or Auctioneer(
        name="Headless Auctioneer", accuracy=cfg.auctioneer.default_accuracy, bias=cfg.auctioneer.bias_by_category
    )

    runs_per_mood = runs
    shared_auction_house = auction_house

    if team_factory is None:
        teams = _default_teams(rng)
    else:
        teams = team_factory(rng)

    all_episode_results: list[EpisodeResult] = []
    for _ in range(runs_per_mood):
        current_house = shared_auction_house or AuctionHouse.generate(rng, cfg=cfg)
        episode_result = run_episode(
            rng,
            runs_per_team=items_per_team,
            pricing_style=pricing_style,
            negotiate_chance=negotiate_chance,
            negotiate_min=negotiate_min,
            negotiate_max=negotiate_max,
            teams=teams,
            factory=factory,
            auctioneer=auctioneer,
            auction_house=current_house,
            cfg=cfg,
        )
        all_episode_results.append(episode_result)

    if csv_path:
        _save_episode_csv(all_episode_results, csv_path, seed=seed)

    return _aggregate(all_episode_results, cfg=cfg, seed=seed, pricing_style=pricing_style)


def _aggregate(episodes: list[EpisodeResult], *, cfg: BalanceConfig, seed: int, pricing_style: str) -> dict:
    all_lot_profits: list[float] = []
    all_appraisal_ratios: list[float] = []
    all_auction_ratios: list[float] = []
    team_profits: list[float] = []
    gavel_metrics = GavelMetrics()
    negotiation_discounts: list[float] = []
    negotiation_success: int = 0
    negotiation_total: int = 0
    mood_counts: dict[str, int] = {}

    for ep in episodes:
        gavel_metrics.eligible += 1
        if ep.gavel_awarded:
            gavel_metrics.awards += 1
        mood_counts[ep.mood] = mood_counts.get(ep.mood, 0) + 1
        negotiation_discounts.extend(ep.negotiation_discounts)
        negotiation_success += ep.negotiation_successes
        negotiation_total += ep.negotiation_total
        for tr in ep.team_results:
            team_profits.append(tr.profit_total)
            for lot in tr.lots:
                all_lot_profits.append(lot.profit)
                if lot.paid:
                    all_appraisal_ratios.append(lot.appraised / lot.paid)
                    all_auction_ratios.append(lot.sold / lot.paid)

    return {
        "meta": {"seed": seed, "pricing_style": pricing_style},
        "config": cfg.to_dict(),
        "profit": {"item": summarize_distribution(all_lot_profits), "team": summarize_distribution(team_profits)},
        "appraisal_ratio": summarize_distribution(all_appraisal_ratios),
        "auction_ratio": summarize_distribution(all_auction_ratios),
        "negotiation": {
            "success_rate": negotiation_success / negotiation_total if negotiation_total else 0.0,
            "discounts": summarize_distribution(negotiation_discounts),
        },
        "gavel": gavel_metrics.to_dict(),
        "moods": mood_counts,
    }


def _default_teams(rng: RNG) -> list[Team]:
    base_contestants = [
        SimpleNamespace(name="Alex", role="Captain", confidence=0.6, taste=0.55),
        SimpleNamespace(name="Jamie", role="Spotter", confidence=0.55, taste=0.6),
    ]
    expert = SimpleNamespace(name="Headless Expert", negotiation_bonus=0.05, signature_style="Generalist")

    def _make_team(name: str, color: tuple[int, int, int]):
        return Team(
            name=name,
            color=color,
            budget_start=400.0,
            budget_left=400.0,
            strategy=None,
            expert=expert,
            contestants=[SimpleNamespace(**vars(c)) for c in base_contestants],
            x=0.0,
            y=0.0,
        )

    return [_make_team("Team A", (220, 60, 60)), _make_team("Team B", (60, 120, 220))]


def _save_episode_csv(episodes: list[EpisodeResult], path: str | Path, *, seed: int):
    import csv

    rows = episodes_to_rows(episodes, seed=seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def save_report(report: dict, path: str | Path):
    import json

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")
