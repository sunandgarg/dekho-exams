"""Point assignments and half-open sums over a huge, mostly empty coordinate span."""

from dataclasses import dataclass


@dataclass
class SumNode:
    total: int = 0
    left: "SumNode | None" = None
    right: "SumNode | None" = None


class SparseMeterIndex:
    def __init__(self, coordinate_limit: int):
        if coordinate_limit <= 0:
            raise ValueError("coordinate_limit must be positive")
        self.coordinate_limit = coordinate_limit
        self.root = SumNode()
        self.values: dict[int, int] = {}

    def assign(self, meter_position: int, reading: int) -> None:
        if not 0 <= meter_position < self.coordinate_limit:
            raise IndexError(meter_position)
        previous = self.values.get(meter_position, 0)
        difference = reading - previous
        if difference == 0:
            return
        if reading:
            self.values[meter_position] = reading
        else:
            self.values.pop(meter_position, None)
        node = self.root
        low, high = 0, self.coordinate_limit
        while True:
            node.total += difference
            if high - low == 1:
                break
            middle = (low + high) // 2
            if meter_position < middle:
                if node.left is None:
                    node.left = SumNode()
                node, high = node.left, middle
            else:
                if node.right is None:
                    node.right = SumNode()
                node, low = node.right, middle

    def sum_between(self, start: int, stop: int) -> int:
        if not 0 <= start <= stop <= self.coordinate_limit:
            raise IndexError((start, stop))

        def visit(node: SumNode | None, low: int, high: int) -> int:
            if node is None or stop <= low or high <= start:
                return 0
            if start <= low and high <= stop:
                return node.total
            middle = (low + high) // 2
            return visit(node.left, low, middle) + visit(node.right, middle, high)

        return visit(self.root, 0, self.coordinate_limit)


meter_index = SparseMeterIndex(1 << 40)
meter_index.assign(47, 19)
meter_index.assign((1 << 39) + 61, 26)
meter_index.assign(47, 52)
print(meter_index.sum_between(0, 100))
print(meter_index.sum_between(0, 1 << 40))
meter_index.assign(47, 0)
print(meter_index.sum_between(0, 100))
