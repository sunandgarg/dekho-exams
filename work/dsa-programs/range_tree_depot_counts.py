from bisect import bisect_left


class RangeNode:
    def __init__(self, points):
        self.low_x = points[0][0]
        self.high_x = points[-1][0]
        self.ys = sorted(point[1] for point in points)
        self.left = self.right = None
        if len(points) > 1:
            middle = len(points) // 2
            self.left = RangeNode(points[:middle])
            self.right = RangeNode(points[middle:])


class DepotRangeTree:
    def __init__(self, points):
        ordered = sorted(points)
        if len({point[2] for point in ordered}) != len(ordered):
            raise ValueError("duplicate depot ID")
        self.root = RangeNode(ordered) if ordered else None

    def count(self, x_low, x_high, y_low, y_high):
        if x_low > x_high or y_low > y_high:
            raise ValueError("inverted half-open window")

        def visit(node):
            if node is None or node.high_x < x_low or node.low_x >= x_high:
                return 0
            if x_low <= node.low_x and node.high_x < x_high:
                return bisect_left(node.ys, y_high) - bisect_left(node.ys, y_low)
            return visit(node.left) + visit(node.right)

        return visit(self.root)


depots = DepotRangeTree([(47, 52, "pump-47"), (19, 61, "valve-19"),
                         (52, 58, "sensor-61"), (180, 70, "grid-83"),
                         (47, 64, "bay-29")])
print(depots.count(15, 60, 45, 65), depots.count(47, 48, 60, 65))
