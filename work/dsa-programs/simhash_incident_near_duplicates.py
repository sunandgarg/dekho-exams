import hashlib


class IncidentFingerprintIndex:
    def __init__(self, band_count=8):
        if not isinstance(band_count, int) or not 1 <= band_count <= 64 or 64 % band_count:
            raise ValueError("band count must divide 64")
        self.band_count = band_count
        self.band_width = 64 // band_count
        self.fingerprints = {}
        self.buckets = {}

    @staticmethod
    def fingerprint(features):
        if not features or any(not isinstance(token, str) or not isinstance(weight, int) or weight <= 0
                               for token, weight in features.items()):
            raise ValueError("features need positive integer weights")
        balance = [0] * 64
        for token, weight in features.items():
            digest = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "little")
            for bit in range(64):
                balance[bit] += weight if digest & (1 << bit) else -weight
        return sum(1 << bit for bit, score in enumerate(balance) if score > 0)

    def _bands(self, fingerprint):
        mask = (1 << self.band_width) - 1
        return [(band, (fingerprint >> (band * self.band_width)) & mask)
                for band in range(self.band_count)]

    def add(self, incident_id, features):
        if incident_id in self.fingerprints:
            raise ValueError("incident ID already indexed")
        fingerprint = self.fingerprint(features)
        self.fingerprints[incident_id] = fingerprint
        for bucket in self._bands(fingerprint):
            self.buckets.setdefault(bucket, set()).add(incident_id)

    def neighbors(self, features, max_distance=7):
        if not 0 <= max_distance < self.band_count:
            raise ValueError("distance must be below band count for complete candidate recall")
        fingerprint = self.fingerprint(features)
        candidates = set().union(*(self.buckets.get(bucket, set())
                                   for bucket in self._bands(fingerprint)))
        return sorted((incident_id, (fingerprint ^ self.fingerprints[incident_id]).bit_count())
                      for incident_id in candidates
                      if (fingerprint ^ self.fingerprints[incident_id]).bit_count() <= max_distance)


if __name__ == "__main__":
    index = IncidentFingerprintIndex()
    index.add(47, {"dock": 3, "scanner": 2, "timeout": 1})
    index.add(83, {"weather": 4, "road": 2})
    print(index.neighbors({"dock": 3, "scanner": 2, "timeout": 1}))
    print(index.neighbors({"weather": 4, "road": 2}))
