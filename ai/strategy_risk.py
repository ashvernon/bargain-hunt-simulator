from ai.strategy_base import Strategy

class RiskAverseStrategy(Strategy):
    name = "RiskAverse"

    def pick_target_stall(self, market, team, rng, items_per_team: int):
        # Prefer stalls where items are in better condition on average
        best = None
        best_score = float("-inf")
        remaining_slots = items_per_team - team.team_item_count
        min_expected_price = min(12.0, market.min_item_price(default=12.0))
        for st in market.stalls:
            if team.stall_cooldowns.get(st.stall_id, 0) > 0:
                continue
            if not st.items:
                continue
            avg_cond = sum(it.condition for it in st.items) / len(st.items)
            has_affordable = any(
                team.spend_plan
                and team.spend_plan.allows_purchase(
                    price=it.shop_price,
                    purchase_index=team.team_item_count,
                    budget_start=team.budget_start,
                    budget_left=team.budget_left,
                    remaining_slots=remaining_slots,
                    min_expected_price=min_expected_price,
                )
                for it in st.items
            )
            if not has_affordable:
                continue
            taste_pull = team.stall_taste_score(st)
            score = avg_cond + taste_pull + rng.uniform(0, 0.1)
            if score > best_score:
                best_score, best = score, st
        return best

    def decide_purchase(self, market, team, stall, rng, items_per_team: int):
        # Still expert-guided, but refuse low condition items
        min_expected_price = min(12.0, market.min_item_price(default=12.0))
        remaining_slots = items_per_team - team.team_item_count
        candidates = [
            it
            for it in stall.items
            if it.condition >= 0.55
            and team.spend_plan
            and team.spend_plan.allows_purchase(
                price=it.shop_price,
                purchase_index=team.team_item_count,
                budget_start=team.budget_start,
                budget_left=team.budget_left,
                remaining_slots=remaining_slots,
                min_expected_price=min_expected_price,
            )
        ]
        if not candidates:
            return None

        best = None
        best_score = float("-inf")
        for rec in candidates:
            est = team.expert.estimate_value(rec, rng)
            margin = est - rec.shop_price
            target_margin = 6.0 - team.average_confidence
            target_margin -= team.style_affinity(rec)
            if margin > max(3.5, target_margin):
                score = margin + rec.condition
                if score > best_score:
                    best_score, best = score, rec
        return best
