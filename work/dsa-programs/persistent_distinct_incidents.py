class PositionNode:
    __slots__ = ("count", "left", "right")

    def __init__(self, count=0, left=None, right=None):
        self.count = count
        self.left = left
        self.right = right


def empty_positions(low, high):
    if high - low == 1:
        return PositionNode()
    middle = (low + high) // 2
    return PositionNode(0, empty_positions(low, middle), empty_positions(middle, high))


def set_latest(previous, low, high, position, active):
    if high - low == 1:
        return PositionNode(active)
    middle = (low + high) // 2
    if position < middle:
        left = set_latest(previous.left, low, middle, position, active)
        right = previous.right
    else:
        left = previous.left
        right = set_latest(previous.right, middle, high, position, active)
    return PositionNode(left.count + right.count, left, right)


def count_latest(node, low, high, left, right):
    if right <= low or high <= left:
        return 0
    if left <= low and high <= right:
        return node.count
    middle = (low + high) // 2
    return (count_latest(node.left, low, middle, left, right)
            + count_latest(node.right, middle, high, left, right))


class DistinctIncidentIndex:
    def __init__(self, incident_codes):
        if not incident_codes:
            raise ValueError("at least one incident is required")
        self.length = len(incident_codes)
        self.roots = [empty_positions(0, self.length)]
        last_position = {}
        for position, code in enumerate(incident_codes):
            root = self.roots[-1]
            if code in last_position:
                root = set_latest(root, 0, self.length, last_position[code], 0)
            root = set_latest(root, 0, self.length, position, 1)
            self.roots.append(root)
            last_position[code] = position

    def distinct_count(self, left, right):
        if not 0 <= left <= right <= self.length:
            raise IndexError("range outside incident log")
        return count_latest(self.roots[right], 0, self.length, left, right)


incident_codes = ["A-47", "B-19", "A-47", "C-61", "B-19", "D-83"]
incidents = DistinctIncidentIndex(incident_codes)
print(incidents.distinct_count(0, 5), incidents.distinct_count(2, 6))
print(incidents.distinct_count(3, 3), incidents.distinct_count(1, 4))
