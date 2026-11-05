import hashlib


class ReplicaDifferenceTable:
    def __init__(self, cells=47, probes=3):
        if cells < probes or probes < 2:
            raise ValueError("need at least one cell per probe")
        self.cells = cells
        self.probes = probes
        self.counts = [0] * cells
        self.keys = [0] * cells
        self.checks = [0] * cells

    def _digest(self, key, salt):
        data = key.to_bytes(8, "little") + salt.to_bytes(2, "little")
        return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "little")

    def _positions(self, key):
        positions = []
        salt = 0
        while len(positions) < self.probes:
            slot = self._digest(key, salt) % self.cells
            if slot not in positions:
                positions.append(slot)
            salt += 1
        return positions

    def adjust(self, key, sign):
        if not isinstance(key, int) or not 0 <= key < 2**64 or sign not in (-1, 1):
            raise ValueError("key must be an unsigned 64-bit ID and sign must be +1 or -1")
        fingerprint = self._digest(key, 65535)
        for slot in self._positions(key):
            self.counts[slot] += sign
            self.keys[slot] ^= key
            self.checks[slot] ^= fingerprint

    def decode(self):
        counts, keys, checks = self.counts[:], self.keys[:], self.checks[:]
        left_only, right_only = set(), set()
        while True:
            pure = next((slot for slot, count in enumerate(counts)
                         if abs(count) == 1 and checks[slot] == self._digest(keys[slot], 65535)
                         and slot in self._positions(keys[slot])), None)
            if pure is None:
                break
            key, sign = keys[pure], counts[pure]
            (left_only if sign == 1 else right_only).add(key)
            fingerprint = self._digest(key, 65535)
            for slot in self._positions(key):
                counts[slot] -= sign
                keys[slot] ^= key
                checks[slot] ^= fingerprint
        if any(count or key or check for count, key, check in zip(counts, keys, checks)):
            return None
        return left_only, right_only


if __name__ == "__main__":
    left = {19, 29, 47, 61}
    right = {19, 47, 83}
    table = ReplicaDifferenceTable()
    for incident_id in left:
        table.adjust(incident_id, 1)
    for incident_id in right:
        table.adjust(incident_id, -1)
    result = table.decode()
    print(tuple(sorted(side) for side in result) if result is not None else None)
