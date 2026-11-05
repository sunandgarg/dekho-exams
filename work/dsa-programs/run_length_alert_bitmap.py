class AlertBitmap:
    def __init__(self, runs=()):
        ordered = sorted(runs)
        merged = []
        for start, end in ordered:
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                raise ValueError("runs must be nonnegative half-open integer intervals")
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        self.runs = tuple(merged)

    def union(self, other):
        return AlertBitmap(self.runs + other.runs)

    def intersection(self, other):
        left = right = 0
        overlap = []
        while left < len(self.runs) and right < len(other.runs):
            start = max(self.runs[left][0], other.runs[right][0])
            end = min(self.runs[left][1], other.runs[right][1])
            if start < end:
                overlap.append((start, end))
            if self.runs[left][1] < other.runs[right][1]:
                left += 1
            else:
                right += 1
        return AlertBitmap(overlap)

    def difference(self, other):
        remaining = []
        right = 0
        for start, end in self.runs:
            cursor = start
            while right < len(other.runs) and other.runs[right][1] <= cursor:
                right += 1
            scan = right
            while scan < len(other.runs) and other.runs[scan][0] < end:
                cut_start, cut_end = other.runs[scan]
                if cursor < cut_start:
                    remaining.append((cursor, min(cut_start, end)))
                cursor = max(cursor, cut_end)
                if cursor >= end:
                    break
                scan += 1
            if cursor < end:
                remaining.append((cursor, end))
        return AlertBitmap(remaining)

    def contains(self, alert_number):
        left, right = 0, len(self.runs)
        while left < right:
            middle = (left + right) // 2
            if self.runs[middle][0] <= alert_number:
                left = middle + 1
            else:
                right = middle
        return left > 0 and alert_number < self.runs[left - 1][1]

    def cardinality(self):
        return sum(end - start for start, end in self.runs)


north_alerts = AlertBitmap([(19, 29), (29, 47), (83, 91)])
east_alerts = AlertBitmap([(23, 31), (43, 61)])
print("shared runs:", north_alerts.intersection(east_alerts).runs)
print("north only:", north_alerts.difference(east_alerts).runs)
print("union count:", north_alerts.union(east_alerts).cardinality())
