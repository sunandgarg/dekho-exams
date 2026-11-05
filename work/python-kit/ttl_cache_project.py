from collections import OrderedDict

class ReceiptTTL:
    def __init__(self, clock):
        self.clock, self.last = clock, -1
        self.entries = OrderedDict()
    def timestamp(self):
        now = self.clock()
        if type(now) is not int or not 0 <= now <= 1000000 or now < self.last:
            raise ValueError("bounded nondecreasing clock required")
        return now
    def expire(self, now):
        for key in [key for key, (_, until) in self.entries.items() if until <= now]:
            del self.entries[key]
        self.last = now
    def put(self, key, amount, ttl):
        if type(key) is not str or not key.isascii() or not key.isalnum() or not 1 <= len(key) <= 16 or type(amount) is not int or not 0 <= amount <= 1000000 or type(ttl) is not int or not 1 <= ttl <= 100:
            raise ValueError("bounded receipt fields required")
        now = self.timestamp()
        self.expire(now)
        self.entries[key] = (amount, now + ttl)
        self.entries.move_to_end(key)
        if len(self.entries) > 4:
            self.entries.popitem(last=False)
    def get(self, key):
        if type(key) is not str or not key.isascii() or not key.isalnum() or not 1 <= len(key) <= 16:
            raise ValueError("bounded key required")
        now = self.timestamp()
        self.expire(now)
        record = self.entries.get(key)
        return None if record is None else record[0]

ticks = [100]
cache = ReceiptTTL(lambda: ticks[0])
cache.put("R41", 125, 10)
ticks[0] = 109
print("before expiry:", cache.get("R41"))
ticks[0] = 110
print("at expiry:", cache.get("R41"))
cache.put("R41", 250, 5)
ticks[0] = 109
try:
    cache.get("R41")
except ValueError:
    print("clock reversal rejected")
print("retained:", list(cache.entries))
