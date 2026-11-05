from collections import deque


class ResidentHistoryCache:
    def __init__(self, capacity, reference_count):
        if capacity < 1 or reference_count < 2:
            raise ValueError("capacity must be positive and reference count at least two")
        self.capacity = capacity
        self.reference_count = reference_count
        self.clock = 0
        self.residents = {}
        self.histories = {}

    def _record(self, case_id):
        self.clock += 1
        self.histories[case_id].append(self.clock)

    def read(self, case_id):
        if case_id not in self.residents:
            raise KeyError(case_id)
        self._record(case_id)
        return self.residents[case_id]

    def put(self, case_id, payload):
        if case_id in self.residents:
            self.residents[case_id] = payload
            self._record(case_id)
            return None
        victim = None
        if len(self.residents) == self.capacity:
            def rank(resident_id):
                history = self.histories[resident_id]
                kth = history[0] if len(history) == self.reference_count else -1
                return (kth, history[-1], resident_id)
            victim = min(self.residents, key=rank)
            del self.residents[victim]
            del self.histories[victim]
        self.residents[case_id] = payload
        self.histories[case_id] = deque(maxlen=self.reference_count)
        self._record(case_id)
        return victim


cache = ResidentHistoryCache(capacity=3, reference_count=2)
for case_id in (47, 19, 61):
    cache.put(case_id, f"case-{case_id}")
cache.read(47)
cache.read(61)
print(cache.put(83, "case-83"))
print(sorted(cache.residents))
print(cache.read(47))
