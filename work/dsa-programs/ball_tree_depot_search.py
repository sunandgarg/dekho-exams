from math import dist


class DepotBall:
    def __init__(self, depots, leaf_size):
        dimensions = len(depots[0][1])
        self.center = tuple(sum(point[axis] for _, point in depots) / len(depots)
                            for axis in range(dimensions))
        self.radius = max(dist(self.center, point) for _, point in depots)
        self.left = None
        self.right = None
        self.depots = None
        if len(depots) <= leaf_size:
            self.depots = depots
        else:
            spread = [max(point[axis] for _, point in depots) - min(point[axis] for _, point in depots)
                      for axis in range(dimensions)]
            axis = max(range(dimensions), key=lambda position: spread[position])
            ordered = sorted(depots, key=lambda depot: depot[1][axis])
            middle = len(ordered) // 2
            self.left = DepotBall(ordered[:middle], leaf_size)
            self.right = DepotBall(ordered[middle:], leaf_size)

    def lower_bound(self, query):
        return max(0.0, dist(self.center, query) - self.radius)


class DepotBallIndex:
    def __init__(self, depots, leaf_size=2):
        if not depots or leaf_size < 1:
            raise ValueError("nonempty depots and positive leaf size required")
        dimensions = len(depots[0][1])
        if dimensions < 1 or any(len(point) != dimensions for _, point in depots):
            raise ValueError("consistent positive dimension required")
        self.root = DepotBall(list(depots), leaf_size)
        self.dimensions = dimensions

    def nearest(self, query):
        if len(query) != self.dimensions:
            raise ValueError("query dimension mismatch")
        best = None

        def visit(node):
            nonlocal best
            if best is not None and node.lower_bound(query) > best[0] + 1e-12:
                return
            if node.depots is not None:
                for depot_id, point in node.depots:
                    candidate = (dist(query, point), depot_id)
                    if best is None or candidate < best:
                        best = candidate
                return
            children = sorted((node.left, node.right), key=lambda child: child.lower_bound(query))
            for child in children:
                visit(child)

        visit(self.root)
        return best[1], round(best[0], 3)


depot_points = [
    ("D-19", (0, 0)), ("D-47", (4, 1)), ("D-61", (9, 0)),
    ("D-83", (4, 7)), ("D-29", (-3, 5)), ("D-37", (10, 8)),
]
depot_index = DepotBallIndex(depot_points)
print(depot_index.nearest((5, 2)), depot_index.nearest((8, 1)))
print(depot_index.nearest((0, 4)))
