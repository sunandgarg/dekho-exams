"""Static, packed rectangle index with exact intersection filtering."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Rectangle:
    west: int
    south: int
    east: int
    north: int

    def __post_init__(self):
        if self.west > self.east or self.south > self.north:
            raise ValueError("rectangle bounds are reversed")

    def intersects(self, other: "Rectangle") -> bool:
        return not (self.east < other.west or other.east < self.west or
                    self.north < other.south or other.north < self.south)


def enclosing(rectangles: list[Rectangle]) -> Rectangle:
    return Rectangle(min(box.west for box in rectangles), min(box.south for box in rectangles),
                     max(box.east for box in rectangles), max(box.north for box in rectangles))


@dataclass
class SpatialNode:
    bounds: Rectangle
    children: list
    leaf: bool


class PackedDepotIndex:
    def __init__(self, depots: list[tuple[str, Rectangle]], fanout: int = 4):
        if fanout < 2:
            raise ValueError("fanout must be at least two")
        if len({depot_id for depot_id, _ in depots}) != len(depots):
            raise ValueError("depot IDs must be distinct")
        self.fanout = fanout
        if not depots:
            self.root = None
            return
        level = [SpatialNode(enclosing([box for _, box in group]), group, True)
                 for group in self._groups(depots, lambda depot: depot[1])]
        while len(level) > 1:
            level = [SpatialNode(enclosing([child.bounds for child in group]), group, False)
                     for group in self._groups(level, lambda node: node.bounds)]
        self.root = level[0]

    def _groups(self, items: list, bounds_of):
        group_count = math.ceil(len(items) / self.fanout)
        slices = math.ceil(math.sqrt(group_count))
        slice_size = math.ceil(len(items) / slices)
        by_x = sorted(items, key=lambda item: (bounds_of(item).west + bounds_of(item).east,
                                               bounds_of(item).south + bounds_of(item).north))
        for start in range(0, len(by_x), slice_size):
            strip = sorted(by_x[start:start + slice_size],
                           key=lambda item: (bounds_of(item).south + bounds_of(item).north,
                                             bounds_of(item).west + bounds_of(item).east))
            for group_start in range(0, len(strip), self.fanout):
                yield strip[group_start:group_start + self.fanout]

    def search(self, query: Rectangle) -> list[str]:
        if self.root is None:
            return []
        matches = []
        pending = [self.root]
        while pending:
            node = pending.pop()
            if not node.bounds.intersects(query):
                continue
            if node.leaf:
                matches.extend(depot_id for depot_id, box in node.children if box.intersects(query))
            else:
                pending.extend(node.children)
        return sorted(matches)


depots = [
    ("D-19", Rectangle(4, 5, 11, 12)),
    ("D-26", Rectangle(18, 7, 26, 14)),
    ("D-47", Rectangle(9, 10, 16, 19)),
    ("D-61", Rectangle(42, 40, 48, 49)),
    ("D-83", Rectangle(12, 2, 20, 8)),
]
depot_index = PackedDepotIndex(depots, fanout=2)
print(depot_index.search(Rectangle(10, 8, 19, 15)))
print(depot_index.search(Rectangle(30, 30, 35, 35)))
