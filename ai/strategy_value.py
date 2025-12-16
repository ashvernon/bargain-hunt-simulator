from ai.strategy_base import Strategy

class ValueHunterStrategy(Strategy):
    name = "ValueHunter"

    def pick_target_stall(self, market, team, rng, items_per_team: int):
        best = None
        best_score = float("-inf")
        fallback = None
        fallback_price = float("inf")
        affordable_needed = items_per_team - team.team_item_count
        min_expected_price = min(12.0, market.min_item_price(default=12.0))
        for st in market.stalls:
            if team.stall_cooldowns.get(st.stall_id, 0) > 0:
                continue
            if not st.items:
                continue
            affordable = sum(
                1
                for it in st.items
                if team.spend_plan and team.spend_plan.allows_purchase(
                    price=it.shop_price,
                    purchase_index=team.team_item_count,
                    budget_start=team.budget_start,
                    budget_left=team.budget_left,
                    remaining_slots=affordable_needed,
                    min_expected_price=min_expected_price,
                )
            )
            if affordable == 0:
                cheapest = min((it.shop_price for it in st.items), default=float("inf"))
                if cheapest < fallback_price:
                    fallback_price, fallback = cheapest, st
                continue
            taste_pull = team.stall_taste_score(st)
            confidence_push = team.average_confidence * 0.6
            score = affordable + taste_pull + confidence_push + rng.uniform(0, 0.25)
            if score > best_score:
                best_score, best = score, st
        return best or fallback

    def decide_purchase(self, market, team, stall, rng, items_per_team: int):
        min_expected_price = min(12.0, market.min_item_price(default=12.0))
        remaining_slots = items_per_team - team.team_item_count
        candidates = [
            it
            for it in stall.items
            if team.spend_plan
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
            style_bonus = team.style_affinity(rec)
            margin = est - rec.shop_price
            target_margin = 12.0 - style_bonus * 4.0
            target_margin -= team.average_confidence * 1.5
            if margin > max(6.0, target_margin):
                score = margin + style_bonus
                if score > best_score:
                    best_score, best = score, rec

        return best
