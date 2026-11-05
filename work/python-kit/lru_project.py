from collections import OrderedDict
import re

class ReceiptCache:
    def __init__(self, capacity):
        if type(capacity) is not int or not 1 <= capacity <= 16:
            raise ValueError("capacity rejected")
        self.capacity = capacity; self.entries = OrderedDict()
    def _key(self, key):
        if not isinstance(key, str) or re.fullmatch(r"R-[0-9]{4}", key) is None:
            raise ValueError("cache key rejected")
    def get(self, key):
        self._key(key)
        if key not in self.entries: return None
        self.entries.move_to_end(key)
        return self.entries[key]
    def put(self, key, amount):
        self._key(key)
        if type(amount) is not int or not 0 <= amount <= 1000000:
            raise ValueError("cache amount rejected")
        self.entries[key] = amount; self.entries.move_to_end(key)
        if len(self.entries) > self.capacity: self.entries.popitem(last=False)

cache = ReceiptCache(2)
cache.put("R-0041", 125); cache.put("R-0042", 250)
print("hit:", cache.get("R-0041"))
cache.put("R-0043", 75)
print("evicted miss:", cache.get("R-0042"))
cache.put("R-0041", 150)
print("retained order:", list(cache.entries))
print("updated:", cache.get("R-0041"))
