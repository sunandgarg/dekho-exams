from bisect import bisect_left
from collections import defaultdict
from math import isqrt


class StaticReadingModes:
    def __init__(self, readings):
        self.readings = list(readings)
        self.length = len(readings)
        self.block_size = max(1, isqrt(self.length))
        self.block_count = (self.length + self.block_size - 1) // self.block_size
        self.positions = defaultdict(list)
        for position, reading in enumerate(readings):
            if not isinstance(reading, int):
                raise TypeError("integer readings required")
            self.positions[reading].append(position)
        self.core_mode = [[None] * self.block_count for _ in range(self.block_count)]
        for first_block in range(self.block_count):
            frequency = defaultdict(int)
            best_value, best_count = None, 0
            for last_block in range(first_block, self.block_count):
                start = last_block * self.block_size
                stop = min(start + self.block_size, self.length)
                for position in range(start, stop):
                    value = self.readings[position]
                    frequency[value] += 1
                    count = frequency[value]
                    if count > best_count or (count == best_count and value < best_value):
                        best_value, best_count = value, count
                self.core_mode[first_block][last_block] = best_value

    def mode(self, start, stop):
        if not 0 <= start <= stop <= self.length:
            raise ValueError("invalid half-open range")
        if start == stop:
            return None
        first_full = (start + self.block_size - 1) // self.block_size
        after_last_full = stop // self.block_size
        if first_full < after_last_full:
            candidates = {self.core_mode[first_full][after_last_full - 1]}
            candidates.update(self.readings[start:first_full * self.block_size])
            candidates.update(self.readings[after_last_full * self.block_size:stop])
        else:
            candidates = set(self.readings[start:stop])
        def score(value):
            locations = self.positions[value]
            count = bisect_left(locations, stop) - bisect_left(locations, start)
            return count, -value
        return max(candidates, key=score)


mode_index = StaticReadingModes([47, 19, 47, 29, 29, 29, 83, 47, 29, 61, 61, 61, 61])
print("first six:", mode_index.mode(0, 6))
print("last five:", mode_index.mode(8, 13))
print("middle tie:", mode_index.mode(2, 9))
