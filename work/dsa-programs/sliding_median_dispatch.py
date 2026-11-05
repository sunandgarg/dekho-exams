import heapq


class ExpiringMedian:
    def __init__(self):
        self.lower = []
        self.upper = []
        self.side = {}
        self.delayed = set()
        self.seen = set()
        self.lower_live = 0
        self.upper_live = 0

    def _prune(self, heap):
        while heap and heap[0][1] in self.delayed:
            _, event_id = heapq.heappop(heap)
            self.delayed.remove(event_id)

    def _balance(self):
        self._prune(self.lower)
        self._prune(self.upper)
        if self.lower_live > self.upper_live + 1:
            negative_value, event_id = heapq.heappop(self.lower)
            heapq.heappush(self.upper, (-negative_value, event_id))
            self.side[event_id] = "upper"
            self.lower_live -= 1
            self.upper_live += 1
            self._prune(self.lower)
        elif self.lower_live < self.upper_live:
            value, event_id = heapq.heappop(self.upper)
            heapq.heappush(self.lower, (-value, event_id))
            self.side[event_id] = "lower"
            self.upper_live -= 1
            self.lower_live += 1
            self._prune(self.upper)

    def add(self, event_id, value):
        if event_id in self.seen:
            raise ValueError("event ID must be new")
        self.seen.add(event_id)
        self._prune(self.lower)
        if not self.lower or value <= -self.lower[0][0]:
            heapq.heappush(self.lower, (-value, event_id))
            self.side[event_id] = "lower"
            self.lower_live += 1
        else:
            heapq.heappush(self.upper, (value, event_id))
            self.side[event_id] = "upper"
            self.upper_live += 1
        self._balance()

    def remove(self, event_id):
        side = self.side.pop(event_id)
        self.delayed.add(event_id)
        if side == "lower":
            self.lower_live -= 1
            self._prune(self.lower)
        else:
            self.upper_live -= 1
            self._prune(self.upper)
        self._balance()

    def lower_median(self):
        if not self.side:
            return None
        self._prune(self.lower)
        return -self.lower[0][0]


def sliding_lower_medians(readings, width):
    if not 1 <= width <= len(readings):
        raise ValueError("window width outside stream")
    index = ExpiringMedian()
    answers = []
    for event_id, value in enumerate(readings):
        index.add(event_id, value)
        if event_id >= width:
            index.remove(event_id - width)
        if event_id >= width - 1:
            answers.append(index.lower_median())
    return answers


dispatch_waits = [47, 19, 61, 29, 83, 37, 19]
print(sliding_lower_medians(dispatch_waits, 3))
print(sliding_lower_medians(dispatch_waits, 4))
