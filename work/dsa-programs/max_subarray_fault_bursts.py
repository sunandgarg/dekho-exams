from dataclasses import dataclass


@dataclass(frozen=True)
class BurstSummary:
    total: int
    prefix: int
    suffix: int
    best: int


def combine(left, right):
    if left is None:
        return right
    if right is None:
        return left
    return BurstSummary(
        left.total + right.total,
        max(left.prefix, left.total + right.prefix),
        max(right.suffix, right.total + left.suffix),
        max(left.best, right.best, left.suffix + right.prefix),
    )


class FaultBurstIndex:
    def __init__(self, fault_scores):
        if not fault_scores:
            raise ValueError("at least one score is required")
        self.length = len(fault_scores)
        self.tree = [None] * (4 * self.length)

        def build(node, low, high):
            if high - low == 1:
                score = fault_scores[low]
                self.tree[node] = BurstSummary(score, score, score, score)
                return
            middle = (low + high) // 2
            build(node * 2, low, middle)
            build(node * 2 + 1, middle, high)
            self.tree[node] = combine(self.tree[node * 2], self.tree[node * 2 + 1])

        build(1, 0, self.length)

    def replace(self, position, score):
        if not 0 <= position < self.length:
            raise IndexError(position)

        def change(node, low, high):
            if high - low == 1:
                self.tree[node] = BurstSummary(score, score, score, score)
                return
            middle = (low + high) // 2
            if position < middle:
                change(node * 2, low, middle)
            else:
                change(node * 2 + 1, middle, high)
            self.tree[node] = combine(self.tree[node * 2], self.tree[node * 2 + 1])

        change(1, 0, self.length)

    def best_burst(self, left, right):
        if not 0 <= left < right <= self.length:
            raise IndexError("a nonempty range is required")

        def read(node, low, high):
            if right <= low or high <= left:
                return None
            if left <= low and high <= right:
                return self.tree[node]
            middle = (low + high) // 2
            return combine(read(node * 2, low, middle), read(node * 2 + 1, middle, high))

        return read(1, 0, self.length).best


fault_scores = [-8, 47, -19, 61, -83, 29, 37]
burst_index = FaultBurstIndex(fault_scores)
print(burst_index.best_burst(0, 7))
print(burst_index.best_burst(4, 7))
burst_index.replace(4, -17)
print(burst_index.best_burst(0, 7))
