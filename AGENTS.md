# Agent Guide for Bargain Hunt Simulator

## How to run and sanity-check
- Use Python 3.11+ and install dependencies with `pip install -r requirements.txt` from the repo root.
- Launch the visual simulator locally with `python main.py --seed 42 --market-seconds 300` to verify UI flows (splash → market → expert pick → appraisal → auction → results).
- When adding assets, keep paths relative to the repo root; both `Path.cwd()` and `assets_root` are used to resolve images.

## Code style and structure
- Keep colors, fonts, and surface helpers centralized in `constants.py` and `ui/render` helpers instead of inlining magic values in screens.
- Prefer the existing screen pattern under `ui/screens` and extend `Screen` subclasses rather than creating ad hoc loops.
- Maintain pure functions for sim/math helpers (e.g., `sim/pricing.py`, `sim/scoring.py`) and avoid introducing Pygame dependencies in those modules.

## Testing expectations
- Run `pytest` for fast feedback when touching logic (market generation, scoring, or strategies) and smoke-test `python main.py` for visual changes.
- Keep random seeds deterministic in tests or examples to ensure reproducibility.
