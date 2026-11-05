class BoundingNode:
    def __init__(self, bounds, items=None, left=None, right=None):
        self.bounds = bounds
        self.items = items
        self.left = left
        self.right = right


def intersects(first, second):
    return (first[0] <= second[2] and second[0] <= first[2] and
            first[1] <= second[3] and second[1] <= first[3])


class DepotBoxHierarchy:
    def __init__(self, rectangles, leaf_capacity=2):
        if leaf_capacity < 1:
            raise ValueError("leaf capacity must be positive")
        if len({depot_id for depot_id, _ in rectangles}) != len(rectangles):
            raise ValueError("duplicate rectangle ID")
        if any(x0 > x1 or y0 > y1 for _, (x0, y0, x1, y1) in rectangles):
            raise ValueError("inverted rectangle")
        self.leaf_capacity = leaf_capacity
        self.root = self._build(list(rectangles)) if rectangles else None

    def _build(self, rectangles):
        boxes = [box for _, box in rectangles]
        bounds = (min(box[0] for box in boxes), min(box[1] for box in boxes),
                  max(box[2] for box in boxes), max(box[3] for box in boxes))
        if len(rectangles) <= self.leaf_capacity:
            return BoundingNode(bounds, items=rectangles)
        axis = 0 if bounds[2] - bounds[0] >= bounds[3] - bounds[1] else 1
        rectangles.sort(key=lambda item: (item[1][axis] + item[1][axis + 2], item[0]))
        middle = len(rectangles) // 2
        return BoundingNode(bounds, left=self._build(rectangles[:middle]),
                            right=self._build(rectangles[middle:]))

    def overlapping(self, query):
        x0, y0, x1, y1 = query
        if x0 > x1 or y0 > y1:
            raise ValueError("inverted query")
        matches = []
        pending = [self.root] if self.root else []
        while pending:
            node = pending.pop()
            if not intersects(node.bounds, query):
                continue
            if node.items is not None:
                matches.extend(depot_id for depot_id, box in node.items
                               if intersects(box, query))
            else:
                pending.extend((node.left, node.right))
        return sorted(matches)


index = DepotBoxHierarchy([
    ("pump-47", (12, 19, 47, 52)), ("valve-19", (45, 25, 61, 58)),
    ("sensor-61", (70, 15, 83, 47)), ("grid-83", (130, 80, 150, 97)),
])
print("overlap=", index.overlapping((40, 40, 75, 55)), sep="")
