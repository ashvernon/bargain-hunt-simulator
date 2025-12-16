class Strategy:
    name = "BaseStrategy"
    def pick_target_stall(self, market, team, rng):
        raise NotImplementedError

    def decide_purchase(self, market, team, stall, rng):
        raise NotImplementedError
