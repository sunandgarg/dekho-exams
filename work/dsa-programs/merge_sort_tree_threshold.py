from bisect import bisect_right
from heapq import merge


class ThresholdCountIndex:
    def __init__(self, readings):
        self.size = len(readings)
        self.nodes = [[] for _ in range(max(1, 4 * self.size))]
        if self.size:
            self._build(1, 0, self.size, readings)

    def _build(self, node, left, right, readings):
        if right - left == 1:
            self.nodes[node] = [readings[left]]
            return
        middle = (left + right) // 2
        self._build(2 * node, left, middle, readings)
        self._build(2 * node + 1, middle, right, readings)
        self.nodes[node] = list(merge(self.nodes[2 * node], self.nodes[2 * node + 1]))

    def count_at_most(self, start, stop, threshold):
        if not 0 <= start <= stop <= self.size:
            raise IndexError("invalid half-open reading range")
        if start == stop:
            return 0
        return self._count(1, 0, self.size, start, stop, threshold)

    def _count(self, node, left, right, start, stop, threshold):
        if stop <= left or right <= start:
            return 0
        if start <= left and right <= stop:
            return bisect_right(self.nodes[node], threshold)
        middle = (left + right) // 2
        return self._count(2 * node, left, middle, start, stop, threshold) + self._count(2 * node + 1, middle, right, start, stop, threshold)


if __name__ == "__main__":
    index = ThresholdCountIndex([41, 18, 41, 73, 26, 55, 12])
    print("at-most-41=", index.count_at_most(1, 6, 41), sep="")
    print("under-26=", index.count_at_most(0, 7, 25), sep="")
    print("empty=", index.count_at_most(4, 4, 41), sep="")
