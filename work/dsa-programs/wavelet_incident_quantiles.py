"""Static wavelet tree for half-open subarray count and selection queries."""

from dataclasses import dataclass


@dataclass
class WaveletNode:
    low: int
    high: int
    left_prefix: list[int]
    left: "WaveletNode | None" = None
    right: "WaveletNode | None" = None


class IncidentQuantiles:
    def __init__(self, latencies: list[int]):
        self.length = len(latencies)
        self.root = self._build(latencies, min(latencies), max(latencies)) if latencies else None

    @classmethod
    def _build(cls, values: list[int], low: int, high: int) -> WaveletNode:
        node = WaveletNode(low, high, [0])
        if low == high:
            node.left_prefix.extend(range(1, len(values) + 1))
            return node
        middle = (low + high) // 2
        smaller, larger = [], []
        for latency in values:
            is_left = latency <= middle
            node.left_prefix.append(node.left_prefix[-1] + is_left)
            (smaller if is_left else larger).append(latency)
        if smaller:
            node.left = cls._build(smaller, low, middle)
        if larger:
            node.right = cls._build(larger, middle + 1, high)
        return node

    def _check_range(self, start: int, stop: int) -> None:
        if not 0 <= start <= stop <= self.length:
            raise IndexError((start, stop))

    def count_below(self, start: int, stop: int, threshold: int) -> int:
        self._check_range(start, stop)

        def visit(node: WaveletNode | None, left: int, right: int) -> int:
            if node is None or left == right or threshold <= node.low:
                return 0
            if node.high < threshold:
                return right - left
            left_start, left_stop = node.left_prefix[left], node.left_prefix[right]
            return (visit(node.left, left_start, left_stop)
                    + visit(node.right, left - left_start, right - left_stop))

        return visit(self.root, start, stop)

    def select(self, start: int, stop: int, ordinal: int) -> int:
        self._check_range(start, stop)
        if not 0 <= ordinal < stop - start:
            raise IndexError(ordinal)
        node = self.root
        while node.low != node.high:
            left_start, left_stop = node.left_prefix[start], node.left_prefix[stop]
            left_count = left_stop - left_start
            if ordinal < left_count:
                node, start, stop = node.left, left_start, left_stop
            else:
                ordinal -= left_count
                node, start, stop = node.right, start - left_start, stop - left_stop
        return node.low


quantiles = IncidentQuantiles([61, 19, 47, 19, 83, 26, 52])
print(quantiles.count_below(1, 6, 47))
print(quantiles.select(1, 6, 2))
print(quantiles.select(0, 7, 6))
