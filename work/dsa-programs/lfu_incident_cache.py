from collections import OrderedDict, defaultdict


class IncidentLFUCache:
    def __init__(self, capacity):
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        self.capacity = capacity
        self.entries = {}
        self.by_frequency = defaultdict(OrderedDict)
        self.minimum_frequency = 0

    def _promote(self, key):
        value, frequency = self.entries[key]
        del self.by_frequency[frequency][key]
        if not self.by_frequency[frequency]:
            del self.by_frequency[frequency]
            if self.minimum_frequency == frequency:
                self.minimum_frequency = frequency + 1
        self.entries[key] = (value, frequency + 1)
        self.by_frequency[frequency + 1][key] = None

    def get(self, key):
        if key not in self.entries:
            return None
        value = self.entries[key][0]
        self._promote(key)
        return value

    def put(self, key, value):
        if self.capacity == 0:
            return None
        if key in self.entries:
            _, frequency = self.entries[key]
            self.entries[key] = (value, frequency)
            self._promote(key)
            return None
        evicted = None
        if len(self.entries) == self.capacity:
            evicted, _ = self.by_frequency[self.minimum_frequency].popitem(last=False)
            del self.entries[evicted]
            if not self.by_frequency[self.minimum_frequency]:
                del self.by_frequency[self.minimum_frequency]
        self.entries[key] = (value, 1)
        self.by_frequency[1][key] = None
        self.minimum_frequency = 1
        return evicted


if __name__ == "__main__":
    cache = IncidentLFUCache(2)
    cache.put("pump-47", "active")
    cache.put("valve-19", "review")
    cache.get("pump-47")
    print("evicted=", cache.put("sensor-61", "active"), sep="")
    print("pump=", cache.get("pump-47"), sep="")
    print("valve=", cache.get("valve-19"), sep="")
