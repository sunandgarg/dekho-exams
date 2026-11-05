class PriorityNode:
    def __init__(self, point, left, right, x_min, x_max):
        self.point, self.left, self.right = point, left, right
        self.x_min, self.x_max = x_min, x_max


class DepotPrioritySearch:
    def __init__(self, events):
        points = list(events)
        if len({point[0] for point in points}) != len(points):
            raise ValueError("event IDs must be unique")
        self.root = self._build(points)

    def _build(self, points):
        if not points:
            return None
        chosen = min(points, key=lambda point: (point[2], point[0]))
        remaining = sorted((point for point in points if point[0] != chosen[0]),
                           key=lambda point: (point[1], point[0]))
        middle = len(remaining) // 2
        left = self._build(remaining[:middle])
        right = self._build(remaining[middle:])
        return PriorityNode(chosen, left, right,
                            min(point[1] for point in points), max(point[1] for point in points))

    def three_sided(self, x_left, x_right, y_limit):
        if x_left > x_right:
            raise ValueError("reversed horizontal range")
        matches = []

        def visit(node):
            if node is None or node.x_max < x_left or node.x_min > x_right:
                return
            if node.point[2] > y_limit:
                return
            event_id, x_position, y_position = node.point
            if x_left <= x_position <= x_right:
                matches.append((event_id, x_position, y_position))
            visit(node.left)
            visit(node.right)

        visit(self.root)
        return sorted(matches)


if __name__ == "__main__":
    events = [("E-19", 19, 47), ("E-29", 29, 17), ("E-47", 47, 61),
              ("E-61", 61, 23), ("E-83", 83, 11)]
    index = DepotPrioritySearch(events)
    print(index.three_sided(20, 70, 30))
    print(index.three_sided(18, 50, 50))
