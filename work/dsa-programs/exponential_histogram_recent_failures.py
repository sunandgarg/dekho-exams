class RecentFailureHistogram:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError("positive window size required")
        self.window_size = window_size
        self.time = 0
        self.buckets = []  # Newest first: (number of ones, oldest one time, newest one time).

    def append(self, failed):
        if failed not in (0, 1, False, True):
            raise ValueError("one binary event required")
        self.time += 1
        if failed:
            self.buckets.insert(0, (1, self.time, self.time))
            self._compress()
        cutoff = self.time - self.window_size + 1
        self.buckets = [bucket for bucket in self.buckets if bucket[2] >= cutoff]

    def _compress(self):
        while True:
            counts = {}
            for bucket in self.buckets:
                counts[bucket[0]] = counts.get(bucket[0], 0) + 1
            oversized = next((size for size in sorted(counts) if counts[size] > 2), None)
            if oversized is None:
                return
            positions = [index for index, bucket in enumerate(self.buckets) if bucket[0] == oversized]
            newer, older = positions[-2:]
            merged = (2 * oversized, self.buckets[older][1], self.buckets[newer][2])
            del self.buckets[older]
            del self.buckets[newer]
            insertion = 0
            while insertion < len(self.buckets) and self.buckets[insertion][2] > merged[2]:
                insertion += 1
            self.buckets.insert(insertion, merged)

    def estimate(self):
        cutoff = self.time - self.window_size + 1
        total = 0.0
        for size, oldest, newest in self.buckets:
            if newest < cutoff:
                continue
            total += size if oldest >= cutoff else size / 2
        return total

    def uncertainty(self):
        """Maximum additive error implied by the one boundary bucket."""
        cutoff = self.time - self.window_size + 1
        return max((size / 2 for size, oldest, newest in self.buckets
                    if oldest < cutoff <= newest), default=0.0)


failure_window = RecentFailureHistogram(8)
for failed in (1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1):
    failure_window.append(failed)
print("estimate:", failure_window.estimate())
print("error allowance:", failure_window.uncertainty())
print("bucket sizes:", [bucket[0] for bucket in failure_window.buckets])
