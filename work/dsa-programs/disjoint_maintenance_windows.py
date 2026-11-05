from bisect import bisect_right


class MaintenanceWindows:
    def __init__(self):
        self.windows = []

    def add(self, start, end):
        if start >= end:
            raise ValueError("window must be nonempty")
        merged = []
        for left, right in sorted(self.windows + [(start, end)]):
            if merged and left <= merged[-1][1]:
                previous_left, previous_right = merged[-1]
                merged[-1] = previous_left, max(previous_right, right)
            else:
                merged.append((left, right))
        self.windows = merged

    def remove(self, start, end):
        if start >= end:
            raise ValueError("window must be nonempty")
        surviving = []
        for left, right in self.windows:
            if right <= start or end <= left:
                surviving.append((left, right))
            else:
                if left < start:
                    surviving.append((left, start))
                if end < right:
                    surviving.append((end, right))
        self.windows = surviving

    def contains(self, instant):
        position = bisect_right(self.windows, (instant, float("inf"))) - 1
        return position >= 0 and instant < self.windows[position][1]

    def covered_length(self):
        return sum(right - left for left, right in self.windows)


if __name__ == "__main__":
    schedule = MaintenanceWindows()
    for start, end in [(19, 47), (61, 83), (47, 61)]:
        schedule.add(start, end)
    print(schedule.windows, schedule.covered_length())
    schedule.remove(29, 71)
    print(schedule.windows, schedule.contains(25), schedule.contains(50))
