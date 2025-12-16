# Bargain Hunt Simulator (Starter Repo)

An AI-driven mini-simulation of a *Bargain Hunt*-style episode. Two teams roam a procedurally generated market, buy antiques with expert guidance, take one last expert pick from the leftovers, then head to appraisal, auction, and scoring.

## Features
- **Procedural fairground:** Each episode builds ten stalls with varied pricing styles, discount behavior, and randomized stock, keeping the shopping phase fresh while respecting starting budgets.【F:models/market.py†L12-L54】【F:config.py†L17-L21】
- **Personality-driven teams:** The Red (ValueHunter strategy) and Blue (RiskAverse strategy) duos rely on contestant confidence/taste plus their dedicated experts for valuations, negotiation boosts, and movement targets.【F:models/episode.py†L29-L86】【F:ai/strategy_value.py†L6-L27】【F:ai/strategy_risk.py†L6-L27】
- **Negotiation and leftover advice:** Purchases include chance-based haggling bonuses and an automatic expert leftover proposal once shopping ends; teams auto-accept or decline based on strategy and remaining budget.【F:models/episode.py†L88-L157】【F:models/episode.py†L183-L216】【F:sim/pricing.py†L3-L18】
- **Appraisal and auction drama:** An independent auctioneer appraises all items before a paced auction sequence that simulates bids, bidder identities, and hammer calls influenced by category demand and mood.【F:models/episode.py†L218-L251】【F:models/auction_house.py†L4-L33】【F:ui/screens/auction_screen.py†L1-L132】
- **Scoreboard with Golden Gavel:** Totals track spend/revenue/profit and award the Golden Gavel when all three team-bought items profit, then declare the winner by profit.【F:sim/scoring.py†L1-L12】【F:models/episode.py†L253-L260】

## Run
1. (Optional) Create a virtual environment.
2. Install dependencies:
   - `pip install pygame moviepy`
3. Launch the simulator:
   - `python main.py`

At startup the app plays an 8-second intro video from `assets/video/into_vid.mp4`; set `show_splash = False` in `config.py` to skip it.

Command-line options let you set the random seed, pick an episode index, and adjust the market timer:

```bash
python main.py --seed 42 --episode 2 --market-minutes 30
# or set seconds directly
python main.py --market-seconds 600
```
【F:main.py†L1-L24】

## Controls
- **SPACE**: Skip to the next phase (market → expert pick → appraisal → auction → results).【F:game_state.py†L27-L48】
- **F**: Cycle simulation speed multipliers (2×, 10×, 20×) during any phase.【F:game_state.py†L62-L77】
- All shopping, expert decisions, appraisals, and auctions run automatically—just sit back and watch the episode unfold.
