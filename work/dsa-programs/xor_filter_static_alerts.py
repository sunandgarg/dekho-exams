from collections import deque
from hashlib import blake2b


class StaticAlertXorFilter:
    def __init__(self, alert_ids):
        keys = sorted(set(alert_ids))
        self.block_size = max(2, (len(keys) * 3 + 3) // 4)
        self.slots = []
        self.seed = None
        if not keys:
            return
        for seed in range(1, 301):
            hashes = [self._hash(key, seed) for key in keys]
            if len(set(hashes)) != len(hashes):
                continue
            degree = [0] * (3 * self.block_size)
            neighbors = [0] * (3 * self.block_size)
            for hashed in hashes:
                for position in self._positions(hashed):
                    degree[position] += 1
                    neighbors[position] ^= hashed
            queue = deque(index for index, count in enumerate(degree) if count == 1)
            peel = []
            while queue:
                position = queue.popleft()
                if degree[position] != 1:
                    continue
                hashed = neighbors[position]
                peel.append((hashed, position))
                for neighbor in self._positions(hashed):
                    degree[neighbor] -= 1
                    neighbors[neighbor] ^= hashed
                    if degree[neighbor] == 1:
                        queue.append(neighbor)
            if len(peel) != len(keys):
                continue
            self.seed = seed
            self.slots = [0] * len(degree)
            for hashed, position in reversed(peel):
                fingerprint = self._fingerprint(hashed)
                for neighbor in self._positions(hashed):
                    if neighbor != position:
                        fingerprint ^= self.slots[neighbor]
                self.slots[position] = fingerprint
            assert all(self.possibly_contains(key) for key in keys)
            return
        raise RuntimeError("could not peel alert set within rebuild budget")

    @staticmethod
    def _hash(alert_id, seed):
        payload = f"{seed}:{alert_id}".encode("utf8")
        return int.from_bytes(blake2b(payload, digest_size=8).digest(), "little")

    def _positions(self, hashed):
        return tuple(group * self.block_size + ((hashed >> (group * 21)) % self.block_size)
                     for group in range(3))

    @staticmethod
    def _fingerprint(hashed):
        return (hashed ^ (hashed >> 32)) & 255

    def possibly_contains(self, alert_id):
        if self.seed is None:
            return False
        hashed = self._hash(alert_id, self.seed)
        combined = 0
        for position in self._positions(hashed):
            combined ^= self.slots[position]
        return combined == self._fingerprint(hashed)


filter_index = StaticAlertXorFilter([47, 19, 61, 83, 29, 103])
print([filter_index.possibly_contains(key) for key in [47, 61, 83]])
print(filter_index.seed, len(filter_index.slots))
