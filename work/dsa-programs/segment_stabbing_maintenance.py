class StabbingWindows:
    def __init__(self, universe_size):
        if universe_size < 1:
            raise ValueError("universe must be positive")
        self.size = universe_size
        self.buckets = [set() for _ in range(4 * universe_size)]
        self.intervals = {}

    def _visit_cover(self, node, low, high, start, end, task_id, adding):
        if end <= low or high <= start:
            return
        if start <= low and high <= end:
            if adding:
                self.buckets[node].add(task_id)
            else:
                self.buckets[node].remove(task_id)
            return
        middle = (low + high) // 2
        self._visit_cover(2 * node, low, middle, start, end, task_id, adding)
        self._visit_cover(2 * node + 1, middle, high, start, end, task_id, adding)

    def add(self, task_id, start, end):
        if task_id in self.intervals:
            raise ValueError("duplicate task ID")
        if not 0 <= start < end <= self.size:
            raise ValueError("interval outside universe")
        self._visit_cover(1, 0, self.size, start, end, task_id, True)
        self.intervals[task_id] = start, end

    def remove(self, task_id):
        start, end = self.intervals.pop(task_id)
        self._visit_cover(1, 0, self.size, start, end, task_id, False)

    def active_at(self, instant):
        if not 0 <= instant < self.size:
            raise ValueError("instant outside universe")
        node, low, high = 1, 0, self.size
        active = set()
        while True:
            active.update(self.buckets[node])
            if high - low == 1:
                return sorted(active)
            middle = (low + high) // 2
            if instant < middle:
                node, high = 2 * node, middle
            else:
                node, low = 2 * node + 1, middle


if __name__ == "__main__":
    schedule = StabbingWindows(128)
    schedule.add("M-19", 19, 61)
    schedule.add("M-47", 47, 83)
    print(schedule.active_at(50), schedule.active_at(83))
    schedule.remove("M-19")
    print(schedule.active_at(50))
