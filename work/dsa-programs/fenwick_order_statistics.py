from bisect import bisect_left


class WeightOrderIndex:
    def __init__(self, allowed_weights):
        self.weights = sorted(set(allowed_weights))
        self.counts = [0] * len(self.weights)
        self.tree = [0] * (len(self.weights) + 1)
        self.total = 0

    def change(self, weight, delta):
        position = bisect_left(self.weights, weight)
        if position == len(self.weights) or self.weights[position] != weight:
            raise KeyError("weight not in declared catalog")
        if self.counts[position] + delta < 0:
            raise ValueError("weight count would become negative")
        self.counts[position] += delta
        self.total += delta
        cursor = position + 1
        while cursor < len(self.tree):
            self.tree[cursor] += delta
            cursor += cursor & -cursor

    def kth(self, one_based_rank):
        if not 1 <= one_based_rank <= self.total:
            raise IndexError("rank outside stored multiset")
        cursor = 0
        bit = 1 << (len(self.weights).bit_length() - 1)
        remaining = one_based_rank
        while bit:
            candidate = cursor + bit
            if candidate < len(self.tree) and self.tree[candidate] < remaining:
                remaining -= self.tree[candidate]
                cursor = candidate
            bit >>= 1
        return self.weights[cursor]

    def count_below(self, weight):
        cursor = bisect_left(self.weights, weight)
        total = 0
        while cursor:
            total += self.tree[cursor]
            cursor -= cursor & -cursor
        return total


if __name__ == "__main__":
    shipments = WeightOrderIndex([-35, 19, 4700, 82000])
    for weight in (4700, -35, 4700, 19, 82000):
        shipments.change(weight, 1)
    print("third=", shipments.kth(3), sep="")
    print("below-4700=", shipments.count_below(4700), sep="")
    shipments.change(4700, -1)
    print("third-after-removal=", shipments.kth(3), sep="")
