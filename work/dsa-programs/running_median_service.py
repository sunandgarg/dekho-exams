"""Append-only exact running median using two heaps."""

import heapq
from fractions import Fraction


class ScanMedian:
    def __init__(self):
        self.lower: list[int] = []
        self.upper: list[int] = []

    def record(self, scan_count: int) -> None:
        if self.lower and scan_count <= -self.lower[0]:
            heapq.heappush(self.lower, -scan_count)
        else:
            heapq.heappush(self.upper, scan_count)
        if len(self.upper) > len(self.lower):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))
        elif len(self.lower) > len(self.upper) + 1:
            heapq.heappush(self.upper, -heapq.heappop(self.lower))

    def median(self) -> Fraction:
        if not self.lower:
            raise ValueError("no scans recorded")
        if len(self.lower) > len(self.upper):
            return Fraction(-self.lower[0])
        return Fraction(-self.lower[0] + self.upper[0], 2)


scan_median = ScanMedian()
for count in (47, 19, 61, 26, 83):
    scan_median.record(count)
print(scan_median.median())
scan_median.record(52)
print(scan_median.median())
