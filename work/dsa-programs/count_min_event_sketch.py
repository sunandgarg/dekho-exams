"""Deterministic row hashes for nonnegative approximate frequency counts."""

import hashlib


class EventCountSketch:
    def __init__(self, width, depth):
        if width < 2 or depth < 1:
            raise ValueError("positive depth and width at least two required")
        self.width = width
        self.depth = depth
        self.counters = [[0] * width for _ in range(depth)]

    def _column(self, event_code, row):
        payload = event_code.encode("utf-8")
        digest = hashlib.blake2b(payload, digest_size=8, person=row.to_bytes(8, "big")).digest()
        return int.from_bytes(digest, "big") % self.width

    def record(self, event_code, amount=1):
        if not isinstance(event_code, str) or not event_code:
            raise ValueError("nonempty event code required")
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("positive integer amount required")
        for row in range(self.depth):
            self.counters[row][self._column(event_code, row)] += amount

    def estimate(self, event_code):
        if not isinstance(event_code, str) or not event_code:
            raise ValueError("nonempty event code required")
        return min(self.counters[row][self._column(event_code, row)] for row in range(self.depth))


frequency = EventCountSketch(width=47, depth=4)
frequency.record("bay-hot", 7)
frequency.record("gate-open", 3)
print(frequency.estimate("bay-hot"))
print(frequency.estimate("gate-open"))
