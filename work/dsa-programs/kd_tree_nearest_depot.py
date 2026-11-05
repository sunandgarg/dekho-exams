"""Balanced two-dimensional k-d tree with exact nearest-neighbor pruning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DepotPoint:
    depot_id: str
    east: int
    north: int


@dataclass(frozen=True)
class SpatialNode:
    point: DepotPoint
    axis: int
    left: "SpatialNode | None"
    right: "SpatialNode | None"


def build_spatial_index(points, depth=0):
    if not points:
        return None
    axis = depth % 2
    ordered = sorted(points, key=lambda point: ((point.east, point.north)[axis], point.depot_id))
    middle = len(ordered) // 2
    return SpatialNode(
        ordered[middle], axis,
        build_spatial_index(ordered[:middle], depth + 1),
        build_spatial_index(ordered[middle + 1:], depth + 1),
    )


def nearest(root, east, north):
    best = None

    def visit(node):
        nonlocal best
        if node is None:
            return
        distance_squared = (node.point.east - east) ** 2 + (node.point.north - north) ** 2
        candidate = (distance_squared, node.point.depot_id)
        if best is None or candidate < best:
            best = candidate
        difference = (east - node.point.east, north - node.point.north)[node.axis]
        nearer, farther = (node.left, node.right) if difference < 0 else (node.right, node.left)
        visit(nearer)
        if best is None or difference * difference <= best[0]:
            visit(farther)

    visit(root)
    return None if best is None else (best[1], best[0])


depots = [DepotPoint("D-19", 4, 9), DepotPoint("D-47", 18, 7), DepotPoint("D-61", 12, 22)]
index = build_spatial_index(depots)
print(nearest(index, 16, 9))
print(nearest(index, 5, 8))
