"""Two Fenwick trees for half-open range addition and range sums."""


class CapacityRangeIndex:
    def __init__(self, capacities: list[int]):
        self.length = len(capacities)
        self.differences = [0] * (self.length + 1)
        self.weighted_differences = [0] * (self.length + 1)
        for position, capacity in enumerate(capacities):
            self.add_between(position, position + 1, capacity)

    def _add(self, tree: list[int], position: int, amount: int) -> None:
        position += 1
        while position <= self.length:
            tree[position] += amount
            position += position & -position

    @staticmethod
    def _prefix(tree: list[int], stop: int) -> int:
        total = 0
        while stop:
            total += tree[stop]
            stop -= stop & -stop
        return total

    def add_between(self, start: int, stop: int, amount: int) -> None:
        if not 0 <= start <= stop <= self.length:
            raise IndexError((start, stop))
        if start == stop:
            return
        self._add(self.differences, start, amount)
        self._add(self.weighted_differences, start, amount * start)
        if stop < self.length:
            self._add(self.differences, stop, -amount)
            self._add(self.weighted_differences, stop, -amount * stop)

    def sum_before(self, stop: int) -> int:
        if not 0 <= stop <= self.length:
            raise IndexError(stop)
        return stop * self._prefix(self.differences, stop) - self._prefix(self.weighted_differences, stop)

    def sum_between(self, start: int, stop: int) -> int:
        if not 0 <= start <= stop <= self.length:
            raise IndexError((start, stop))
        return self.sum_before(stop) - self.sum_before(start)


capacity_index = CapacityRangeIndex([23, 47, 19, 61, 38])
capacity_index.add_between(1, 4, 7)
capacity_index.add_between(3, 5, -4)
print(capacity_index.sum_between(1, 5))
print(capacity_index.sum_between(3, 4))
