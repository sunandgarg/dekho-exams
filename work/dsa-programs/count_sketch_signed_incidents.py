import hashlib
from statistics import median


class SignedIncidentSketch:
    def __init__(self, width=31, rows=5):
        if width <= 0 or rows <= 0 or rows % 2 == 0:
            raise ValueError("positive width and odd positive row count required")
        self.width = width
        self.rows = rows
        self.counters = [[0] * width for _ in range(rows)]

    def _probe(self, incident_key, row):
        payload = f"{row}\0{incident_key}".encode("utf-8")
        digest = hashlib.blake2b(payload, digest_size=16).digest()
        bucket = int.from_bytes(digest[:8], "big") % self.width
        sign = 1 if digest[8] & 1 else -1
        return bucket, sign

    def adjust(self, incident_key, delta):
        if not isinstance(incident_key, str) or not isinstance(delta, int):
            raise TypeError("string key and integer delta required")
        for row in range(self.rows):
            bucket, sign = self._probe(incident_key, row)
            self.counters[row][bucket] += sign * delta

    def estimate(self, incident_key):
        if not isinstance(incident_key, str):
            raise TypeError("string key required")
        readings = []
        for row in range(self.rows):
            bucket, sign = self._probe(incident_key, row)
            readings.append(sign * self.counters[row][bucket])
        return median(readings)


incident_sketch = SignedIncidentSketch(width=29, rows=5)
for key, change in (("scanner", 47), ("dock", 19), ("invoice", 29), ("scanner", -8)):
    incident_sketch.adjust(key, change)
print("scanner estimate:", incident_sketch.estimate("scanner"))
print("dock estimate:", incident_sketch.estimate("dock"))
print("unseen estimate:", incident_sketch.estimate("missing"))
