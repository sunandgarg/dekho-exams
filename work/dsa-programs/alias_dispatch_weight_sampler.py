from math import isfinite
from random import Random


class DispatchSampler:
    def __init__(self, weighted_routes):
        if not weighted_routes:
            raise ValueError("at least one route required")
        self.routes = list(weighted_routes)
        weights = list(weighted_routes.values())
        if any(not isfinite(weight) or weight < 0 for weight in weights):
            raise ValueError("weights must be finite and nonnegative")
        total = sum(weights)
        if not isfinite(total) or total <= 0:
            raise ValueError("positive finite total required")
        route_count = len(weights)
        scaled = [weight * route_count / total for weight in weights]
        small = [index for index, value in enumerate(scaled) if value < 1]
        large = [index for index, value in enumerate(scaled) if value >= 1]
        self.threshold = [1.0] * route_count
        self.alias = list(range(route_count))
        while small and large:
            low = small.pop()
            high = large.pop()
            self.threshold[low] = scaled[low]
            self.alias[low] = high
            scaled[high] = scaled[high] + scaled[low] - 1
            (small if scaled[high] < 1 else large).append(high)

    def pick_from_unit(self, unit):
        """Map one uniform draw in [0,1) into a weighted route."""
        if not 0 <= unit < 1:
            raise ValueError("unit draw outside [0,1)")
        position = unit * len(self.routes)
        column = int(position)
        fraction = position - column
        selected = column if fraction < self.threshold[column] else self.alias[column]
        return self.routes[selected]

    def sample(self, random_source):
        return self.pick_from_unit(random_source.random())


dispatch_sampler = DispatchSampler({"north": 19, "east": 47, "west": 29})
print("fixed draws:", [dispatch_sampler.pick_from_unit(draw) for draw in (0.03, 0.31, 0.69, 0.94)])
print("seeded draws:", [dispatch_sampler.sample(Random(seed)) for seed in (17, 29, 47)])
