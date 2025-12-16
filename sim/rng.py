import random

class RNG:
    def __init__(self, seed: int):
        self._r = random.Random(seed)

    def random(self) -> float:
        return self._r.random()

    def uniform(self, a: float, b: float) -> float:
        return self._r.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        return self._r.randint(a, b)

    def choice(self, seq):
        return self._r.choice(seq)

    def shuffle(self, seq):
        self._r.shuffle(seq)

    def lognormal(self, mean: float = 0.0, sigma: float = 0.35) -> float:
        # Using underlying random.lognormvariate (mu, sigma)
        return self._r.lognormvariate(mean, sigma)
