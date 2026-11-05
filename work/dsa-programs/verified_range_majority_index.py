from bisect import bisect_left
from collections import defaultdict


def combine(left, right):
    left_candidate, left_balance = left
    right_candidate, right_balance = right
    if left_balance == 0:
        return right
    if right_balance == 0:
        return left
    if left_candidate == right_candidate:
        return left_candidate, left_balance + right_balance
    if left_balance > right_balance:
        return left_candidate, left_balance - right_balance
    return right_candidate, right_balance - left_balance


class MajorityWindowIndex:
    def __init__(self, readings):
        self.readings = list(readings)
        self.length = len(readings)
        self.base = 1 << max(0, self.length - 1).bit_length()
        self.tree = [(None, 0)] * (2 * self.base)
        self.positions = defaultdict(list)
        for index, reading in enumerate(readings):
            self.tree[self.base + index] = (reading, 1)
            self.positions[reading].append(index)
        for node in range(self.base - 1, 0, -1):
            self.tree[node] = combine(self.tree[2 * node], self.tree[2 * node + 1])

    def majority(self, start, end):
        if not 0 <= start <= end <= self.length:
            raise ValueError("invalid half-open window")
        left_accumulator = right_accumulator = (None, 0)
        left, right = start + self.base, end + self.base
        while left < right:
            if left & 1:
                left_accumulator = combine(left_accumulator, self.tree[left])
                left += 1
            if right & 1:
                right -= 1
                right_accumulator = combine(self.tree[right], right_accumulator)
            left //= 2
            right //= 2
        candidate, _ = combine(left_accumulator, right_accumulator)
        if candidate is None:
            return None
        locations = self.positions[candidate]
        occurrences = bisect_left(locations, end) - bisect_left(locations, start)
        return candidate if occurrences * 2 > end - start else None


majority_index = MajorityWindowIndex([47, 19, 47, 47, 83, 19, 47, 61])
print("first five:", majority_index.majority(0, 5))
print("last four:", majority_index.majority(4, 8))
print("empty:", majority_index.majority(3, 3))
