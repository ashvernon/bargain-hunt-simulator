from ai.strategy_base import Strategy

class ValueHunterStrategy(Strategy):
    name = "ValueHunter"

    def pick_target_stall(self, market, team, rng):
        # Head to the stall with most affordable items (simple heuristic)
        best = None
        best_score = float("-inf")
        for st in market.stalls:
            affordable = sum(1 for it in st.items if it.shop_price <= team.budget_left)
            score = affordable + rng.uniform(0, 0.25)
            if score > best_score:
                best_score, best = score, st
        return best

    def decide_purchase(self, market, team, stall, rng):
        # Expert guided: ask expert for best margin within this stall
        rec = team.expert.recommend_from_stall(stall, team.budget_left, rng)
        if not rec:
            return None
        est = team.expert.estimate_value(rec, rng)
        if (est - rec.shop_price) > 12.0:
            return rec
        return None
