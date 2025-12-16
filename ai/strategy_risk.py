from ai.strategy_base import Strategy

class RiskAverseStrategy(Strategy):
    name = "RiskAverse"

    def pick_target_stall(self, market, team, rng):
        # Prefer stalls where items are in better condition on average
        best = None
        best_score = float("-inf")
        for st in market.stalls:
            if not st.items:
                continue
            avg_cond = sum(it.condition for it in st.items) / len(st.items)
            score = avg_cond + rng.uniform(0, 0.1)
            if score > best_score:
                best_score, best = score, st
        return best

    def decide_purchase(self, market, team, stall, rng):
        # Still expert-guided, but refuse low condition items
        rec = team.expert.recommend_from_stall(stall, team.budget_left, rng)
        if not rec:
            return None
        if rec.condition < 0.55:
            return None
        est = team.expert.estimate_value(rec, rng)
        if (est - rec.shop_price) > 6.0:
            return rec
        return None
