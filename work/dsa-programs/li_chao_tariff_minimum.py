from dataclasses import dataclass


@dataclass(frozen=True)
class TariffLine:
    slope: int
    intercept: int

    def cost(self, units):
        return self.slope * units + self.intercept


class TariffNode:
    def __init__(self, line):
        self.line = line
        self.left = None
        self.right = None


class LiChaoTariffs:
    def __init__(self, minimum_units, maximum_units):
        if minimum_units > maximum_units:
            raise ValueError("empty integer unit domain")
        self.minimum_units = minimum_units
        self.maximum_units = maximum_units
        self.root = None

    def add_line(self, line):
        self.root = self._insert(self.root, self.minimum_units, self.maximum_units, line)

    def _insert(self, node, left, right, incoming):
        if node is None:
            return TariffNode(incoming)
        middle = (left + right) // 2
        if incoming.cost(middle) < node.line.cost(middle):
            node.line, incoming = incoming, node.line
        if left == right:
            return node
        if incoming.cost(left) < node.line.cost(left):
            node.left = self._insert(node.left, left, middle, incoming)
        elif incoming.cost(right) < node.line.cost(right):
            node.right = self._insert(node.right, middle + 1, right, incoming)
        return node

    def min_cost(self, units):
        if not self.minimum_units <= units <= self.maximum_units:
            raise IndexError("units outside declared domain")
        if self.root is None:
            raise ValueError("no tariff lines have been added")
        node = self.root
        left, right = self.minimum_units, self.maximum_units
        minimum = float("inf")
        while node is not None:
            minimum = min(minimum, node.line.cost(units))
            middle = (left + right) // 2
            if units <= middle:
                node = node.left
                right = middle
            else:
                node = node.right
                left = middle + 1
        return minimum


if __name__ == "__main__":
    tariffs = LiChaoTariffs(0, 80)
    for tariff in (TariffLine(7, 13), TariffLine(4, 49), TariffLine(9, -11)):
        tariffs.add_line(tariff)
    print("units-5=", tariffs.min_cost(5), sep="")
    print("units-35=", tariffs.min_cost(35), sep="")
