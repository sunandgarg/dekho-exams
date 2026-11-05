import hashlib
from collections import Counter


class CountingIncidentFilter:
    def __init__(self, counter_count, hash_count):
        if counter_count < 1 or hash_count < 1:
            raise ValueError("counter and hash counts must be positive")
        self.counters = [0] * counter_count
        self.hash_count = hash_count

    def _positions(self, incident_id):
        encoded = incident_id.encode("utf-8")
        for hash_number in range(self.hash_count):
            digest = hashlib.blake2b(
                encoded + hash_number.to_bytes(4, "big"), digest_size=8
            ).digest()
            yield int.from_bytes(digest, "big") % len(self.counters)

    def add(self, incident_id):
        for position in self._positions(incident_id):
            self.counters[position] += 1

    def remove_known_insert(self, incident_id):
        positions = Counter(self._positions(incident_id))
        if any(self.counters[position] < multiplicity
               for position, multiplicity in positions.items()):
            raise ValueError("insufficient counters")
        for position, multiplicity in positions.items():
            self.counters[position] -= multiplicity

    def might_contain(self, incident_id):
        return all(self.counters[position] > 0
                   for position in self._positions(incident_id))


filter_index = CountingIncidentFilter(127, 4)
filter_index.add("pump-47")
filter_index.add("pump-47")
filter_index.add("valve-19")
filter_index.remove_known_insert("pump-47")
print("pump=", filter_index.might_contain("pump-47"),
      "valve=", filter_index.might_contain("valve-19"), sep="")
