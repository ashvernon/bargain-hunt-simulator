from ai.strategy_base import Strategy

class ValueHunterStrategy(Strategy):
    name = "ValueHunter"

    def pick_target_stall(self, market, team, rng):
        # Head to the stall with most affordable items (simple heuristic)
        best = None
        best_score = float("-inf")
        for st in market.stalls:
            affordable = sum(1 for it in st.items if it.shop_price <= team.budget_left)
            taste_pull = team.stall_taste_score(st)
            confidence_push = team.average_confidence * 0.6
            score = affordable + taste_pull + confidence_push + rng.uniform(0, 0.25)
            if score > best_score:
                best_score, best = score, st
        return best

    def decide_purchase(self, market, team, stall, rng):
        # Expert guided: ask expert for best margin within this stall
        rec = team.expert.recommend_from_stall(stall, team.budget_left, rng)
        if not rec:
            return None
        est = team.expert.estimate_value(rec, rng)
        style_bonus = team.style_affinity(rec)
        margin = est - rec.shop_price
        target_margin = 12.0 - style_bonus * 4.0
        target_margin -= team.average_confidence * 1.5
        if margin > max(6.0, target_margin):
            return rec
        return None
