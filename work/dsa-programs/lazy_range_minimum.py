"""Half-open range additions and minimum queries with deferred updates."""


class CapacityMinimums:
    def __init__(self, capacities: list[int]):
        if not capacities:
            raise ValueError("capacities must be nonempty")
        self.length = len(capacities)
        self.minimum = [0] * (4 * self.length)
        self.pending_add = [0] * (4 * self.length)

        def build(node: int, low: int, high: int) -> None:
            if high - low == 1:
                self.minimum[node] = capacities[low]
                return
            middle = (low + high) // 2
            build(node * 2, low, middle)
            build(node * 2 + 1, middle, high)
            self.minimum[node] = min(self.minimum[node * 2], self.minimum[node * 2 + 1])

        build(1, 0, self.length)

    def _push(self, node: int) -> None:
        amount = self.pending_add[node]
        if amount:
            for child in (node * 2, node * 2 + 1):
                self.minimum[child] += amount
                self.pending_add[child] += amount
            self.pending_add[node] = 0

    def add_between(self, start: int, stop: int, amount: int) -> None:
        if not 0 <= start <= stop <= self.length:
            raise IndexError((start, stop))

        def change(node: int, low: int, high: int) -> None:
            if stop <= low or high <= start:
                return
            if start <= low and high <= stop:
                self.minimum[node] += amount
                self.pending_add[node] += amount
                return
            self._push(node)
            middle = (low + high) // 2
            change(node * 2, low, middle)
            change(node * 2 + 1, middle, high)
            self.minimum[node] = min(self.minimum[node * 2], self.minimum[node * 2 + 1])

        change(1, 0, self.length)

    def minimum_between(self, start: int, stop: int) -> int:
        if not 0 <= start < stop <= self.length:
            raise IndexError((start, stop))

        def query(node: int, low: int, high: int) -> int | None:
            if stop <= low or high <= start:
                return None
            if start <= low and high <= stop:
                return self.minimum[node]
            self._push(node)
            middle = (low + high) // 2
            left = query(node * 2, low, middle)
            right = query(node * 2 + 1, middle, high)
            if left is None:
                return right
            if right is None:
                return left
            return min(left, right)

        return query(1, 0, self.length)


capacity_index = CapacityMinimums([61, 47, 83, 26, 52, 19])
capacity_index.add_between(1, 5, -7)
print(capacity_index.minimum_between(0, 6))
capacity_index.add_between(3, 6, 20)
print(capacity_index.minimum_between(2, 6))
print(capacity_index.minimum_between(0, 3))
