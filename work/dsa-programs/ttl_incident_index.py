from heapq import heappop, heappush


class IncidentExpiryIndex:
    def __init__(self):
        self.clock = 0
        self.serial = 0
        self.entries = {}
        self.expirations = []

    def advance(self, now):
        if now < self.clock:
            raise ValueError("clock cannot move backward")
        self.clock = now
        while self.expirations and self.expirations[0][0] <= now:
            expires_at, serial, key = heappop(self.expirations)
            current = self.entries.get(key)
            if current is not None and current[1:] == (expires_at, serial):
                del self.entries[key]

    def put(self, key, value, now, lifetime):
        if lifetime < 0:
            raise ValueError("lifetime cannot be negative")
        self.advance(now)
        self.serial += 1
        expires_at = now + lifetime
        self.entries[key] = (value, expires_at, self.serial)
        heappush(self.expirations, (expires_at, self.serial, key))
        self.advance(now)

    def get(self, key, now):
        self.advance(now)
        current = self.entries.get(key)
        return None if current is None else current[0]


if __name__ == "__main__":
    index = IncidentExpiryIndex()
    index.put("pump-47", "open", now=23, lifetime=19)
    index.put("pump-47", "rechecked", now=29, lifetime=38)
    print("at-42=", index.get("pump-47", 42), sep="")
    print("at-67=", index.get("pump-47", 67), sep="")
