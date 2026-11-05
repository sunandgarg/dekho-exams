from bisect import bisect_left


class CountNode:
    __slots__ = ("count", "left", "right")

    def __init__(self, count=0, left=None, right=None):
        self.count = count
        self.left = left
        self.right = right


def add_count(previous, low, high, rank):
    if high - low == 1:
        return CountNode(previous.count + 1)
    middle = (low + high) // 2
    if rank < middle:
        changed_left = add_count(previous.left, low, middle, rank)
        return CountNode(previous.count + 1, changed_left, previous.right)
    changed_right = add_count(previous.right, middle, high, rank)
    return CountNode(previous.count + 1, previous.left, changed_right)


def empty_counts(low, high):
    if high - low == 1:
        return CountNode()
    middle = (low + high) // 2
    return CountNode(0, empty_counts(low, middle), empty_counts(middle, high))


class ShipmentRankIndex:
    def __init__(self, priorities):
        if not priorities:
            raise ValueError("at least one priority is required")
        self.values = sorted(set(priorities))
        self.roots = [empty_counts(0, len(self.values))]
        for priority in priorities:
            rank = bisect_left(self.values, priority)
            self.roots.append(add_count(self.roots[-1], 0, len(self.values), rank))

    def kth(self, left, right, position):
        if not 0 <= left < right < len(self.roots):
            raise IndexError("range must be nonempty and inside the array")
        if not 1 <= position <= right - left:
            raise ValueError("position is outside the range")
        before = self.roots[left]
        after = self.roots[right]
        low, high = 0, len(self.values)
        while high - low > 1:
            middle = (low + high) // 2
            left_count = after.left.count - before.left.count
            if position <= left_count:
                before, after, high = before.left, after.left, middle
            else:
                position -= left_count
                before, after, low = before.right, after.right, middle
        return self.values[low]


shipment_priorities = [47, 19, 61, 29, 19, 83, 37]
priority_index = ShipmentRankIndex(shipment_priorities)
print(priority_index.kth(1, 6, 3))
print(priority_index.kth(0, 7, 6))
print(priority_index.kth(2, 5, 2))
