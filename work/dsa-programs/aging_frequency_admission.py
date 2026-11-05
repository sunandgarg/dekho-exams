from collections import OrderedDict
import hashlib


class AgingFrequencySketch:
    def __init__(self, width=16, rows=4, sample_size=64):
        if min(width, rows, sample_size) < 1:
            raise ValueError("sketch dimensions and sample size must be positive")
        self.width = width
        self.counters = [[0] * width for _ in range(rows)]
        self.sample_size = sample_size
        self.samples = 0

    def _columns(self, incident_id):
        digest = hashlib.blake2b(str(incident_id).encode(), digest_size=16).digest()
        for row in range(len(self.counters)):
            yield int.from_bytes(digest[row * 4:row * 4 + 4], "little") % self.width

    def record(self, incident_id):
        for counters, column in zip(self.counters, self._columns(incident_id)):
            counters[column] = min(15, counters[column] + 1)
        self.samples += 1
        if self.samples == self.sample_size:
            for counters in self.counters:
                for column in range(self.width):
                    counters[column] //= 2
            self.samples = 0

    def estimate(self, incident_id):
        return min(counters[column] for counters, column in zip(self.counters, self._columns(incident_id)))


class FrequencyAdmissionCache:
    def __init__(self, capacity=2):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.order = OrderedDict()
        self.sketch = AgingFrequencySketch()

    def get(self, incident_id):
        self.sketch.record(incident_id)
        self.order.move_to_end(incident_id)
        return self.order[incident_id]

    def put(self, incident_id, payload):
        self.sketch.record(incident_id)
        if incident_id in self.order:
            self.order[incident_id] = payload
            self.order.move_to_end(incident_id)
            return True
        if len(self.order) == self.capacity:
            victim_id = next(iter(self.order))
            if self.sketch.estimate(incident_id) <= self.sketch.estimate(victim_id):
                return False
            self.order.popitem(last=False)
        self.order[incident_id] = payload
        return True


cache = FrequencyAdmissionCache(2)
cache.put(47, "incident-47")
cache.put(19, "incident-19")
for _ in range(4):
    cache.get(47)
accepted_cold = cache.put(83, "incident-83")
for _ in range(5):
    cache.sketch.record(61)
accepted_warm = cache.put(61, "incident-61")
print("cold=", accepted_cold, " warm=", accepted_warm,
      " resident=", list(cache.order), sep="")
