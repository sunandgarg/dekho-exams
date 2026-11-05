"""Undirected adjacency bitsets for fixed, dense depot IDs."""


class DepotBitGraph:
    def __init__(self, depot_ids):
        self.depot_ids = tuple(depot_ids)
        if len(set(self.depot_ids)) != len(self.depot_ids):
            raise ValueError("duplicate depot")
        self.position = {depot_id: index for index, depot_id in enumerate(self.depot_ids)}
        self.rows = [0] * len(self.depot_ids)

    def _pair(self, first, second):
        left, right = self.position[first], self.position[second]
        if left == right:
            raise ValueError("self-edge")
        return left, right

    def connect(self, first, second):
        left, right = self._pair(first, second)
        self.rows[left] |= 1 << right
        self.rows[right] |= 1 << left

    def disconnect(self, first, second):
        left, right = self._pair(first, second)
        self.rows[left] &= ~(1 << right)
        self.rows[right] &= ~(1 << left)

    def adjacent(self, first, second):
        left, right = self._pair(first, second)
        return bool(self.rows[left] & (1 << right))

    def common_neighbor_count(self, first, second):
        left, right = self._pair(first, second)
        return (self.rows[left] & self.rows[right]).bit_count()

    def neighbors(self, depot_id):
        row = self.rows[self.position[depot_id]]
        result = []
        while row:
            lowest_bit = row & -row
            result.append(self.depot_ids[lowest_bit.bit_length() - 1])
            row ^= lowest_bit
        return result


graph = DepotBitGraph(("D-19", "D-26", "D-47", "D-61"))
for first, second in (("D-19", "D-26"), ("D-19", "D-47"), ("D-61", "D-26"), ("D-61", "D-47")):
    graph.connect(first, second)
print(graph.common_neighbor_count("D-19", "D-61"))
graph.disconnect("D-19", "D-47")
print(graph.neighbors("D-19"))
print(graph.adjacent("D-19", "D-47"))
