class QuadNode:
    def __init__(self, left, bottom, right, top):
        self.bounds = (left, bottom, right, top)
        self.points = []
        self.children = None


class DepotQuadtree:
    def __init__(self, width=256, capacity=3, max_depth=8):
        if width < 1 or width & (width - 1) or capacity < 1 or max_depth < 0:
            raise ValueError("invalid width, capacity, or depth")
        self.root = QuadNode(0, 0, width, width)
        self.capacity = capacity
        self.max_depth = max_depth
        self.identifiers = set()

    @staticmethod
    def _child(node, x, y):
        left, bottom, right, top = node.bounds
        middle_x, middle_y = (left + right) // 2, (bottom + top) // 2
        return (1 if x >= middle_x else 0) + (2 if y >= middle_y else 0)

    def _insert(self, node, point, depth):
        if node.children is not None:
            self._insert(node.children[self._child(node, point[1], point[2])], point, depth + 1)
            return
        node.points.append(point)
        left, bottom, right, top = node.bounds
        if len(node.points) <= self.capacity or depth >= self.max_depth or right - left == 1:
            return
        middle_x, middle_y = (left + right) // 2, (bottom + top) // 2
        node.children = [QuadNode(left, bottom, middle_x, middle_y),
                         QuadNode(middle_x, bottom, right, middle_y),
                         QuadNode(left, middle_y, middle_x, top),
                         QuadNode(middle_x, middle_y, right, top)]
        pending, node.points = node.points, []
        for previous in pending:
            self._insert(node.children[self._child(node, previous[1], previous[2])],
                         previous, depth + 1)

    def insert(self, depot_id, x, y):
        width = self.root.bounds[2]
        if depot_id in self.identifiers or not (0 <= x < width and 0 <= y < width):
            raise ValueError("duplicate ID or point outside domain")
        self.identifiers.add(depot_id)
        self._insert(self.root, (depot_id, x, y), 0)

    def range_report(self, left, bottom, right, top):
        if not (0 <= left <= right <= self.root.bounds[2] and
                0 <= bottom <= top <= self.root.bounds[3]):
            raise ValueError("invalid query rectangle")
        found = []
        pending = [self.root]
        while pending:
            node = pending.pop()
            x0, y0, x1, y1 = node.bounds
            if left >= x1 or right <= x0 or bottom >= y1 or top <= y0:
                continue
            if node.children is None:
                found.extend(depot_id for depot_id, x, y in node.points
                             if left <= x < right and bottom <= y < top)
            else:
                pending.extend(node.children)
        return sorted(found)


index = DepotQuadtree(capacity=2)
for depot_id, x, y in (("pump-47", 47, 52), ("valve-19", 19, 61),
                       ("sensor-61", 52, 58), ("grid-83", 180, 70)):
    index.insert(depot_id, x, y)
print("window=", index.range_report(15, 45, 60, 65), sep="")
