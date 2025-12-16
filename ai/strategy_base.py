from ai.spend_plan import pick_spend_plan


class Strategy:
    name = "BaseStrategy"

    def pick_target_stall(self, market, team, rng, items_per_team: int):
        raise NotImplementedError

    def decide_purchase(self, market, team, stall, rng, items_per_team: int):
        raise NotImplementedError

    def choose_spend_plan(self, rng):
        return pick_spend_plan(rng)
