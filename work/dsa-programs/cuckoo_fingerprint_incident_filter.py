import hashlib
import random


class FingerprintIncidentFilter:
    def __init__(self, bucket_count=32, bucket_size=2, fingerprint_bits=12,
                 max_kicks=80, seed=47):
        if bucket_count < 2 or bucket_count & (bucket_count - 1):
            raise ValueError("bucket count must be a power of two")
        if bucket_size < 1 or not 4 <= fingerprint_bits <= 32 or max_kicks < 1:
            raise ValueError("invalid bucket, fingerprint, or kick limit")
        self.buckets = [[] for _ in range(bucket_count)]
        self.bucket_size = bucket_size
        self.fingerprint_bits = fingerprint_bits
        self.max_kicks = max_kicks
        self.random_source = random.Random(seed)

    def _alternate(self, bucket_number, fingerprint):
        digest = hashlib.blake2b(fingerprint.to_bytes(4, "big"), digest_size=8).digest()
        offset = (int.from_bytes(digest, "big") & (len(self.buckets) - 1)) or 1
        return bucket_number ^ offset

    def _locations(self, incident_id):
        digest = hashlib.sha256(incident_id.encode("utf-8")).digest()
        fingerprint = (int.from_bytes(digest[:4], "big")
                       & ((1 << self.fingerprint_bits) - 1)) or 1
        first = int.from_bytes(digest[4:12], "big") & (len(self.buckets) - 1)
        return fingerprint, first, self._alternate(first, fingerprint)

    def add(self, incident_id):
        fingerprint, first, second = self._locations(incident_id)
        for bucket_number in (first, second):
            if len(self.buckets[bucket_number]) < self.bucket_size:
                self.buckets[bucket_number].append(fingerprint)
                return True
        bucket_number = self.random_source.choice((first, second))
        displaced_fingerprint = fingerprint
        changes = []
        for _ in range(self.max_kicks):
            slot = self.random_source.randrange(self.bucket_size)
            previous = self.buckets[bucket_number][slot]
            self.buckets[bucket_number][slot] = displaced_fingerprint
            changes.append((bucket_number, slot, previous))
            displaced_fingerprint = previous
            bucket_number = self._alternate(bucket_number, previous)
            if len(self.buckets[bucket_number]) < self.bucket_size:
                self.buckets[bucket_number].append(displaced_fingerprint)
                return True
        for changed_bucket, changed_slot, previous in reversed(changes):
            self.buckets[changed_bucket][changed_slot] = previous
        return False

    def might_contain(self, incident_id):
        fingerprint, first, second = self._locations(incident_id)
        return fingerprint in self.buckets[first] or fingerprint in self.buckets[second]


filter_index = FingerprintIncidentFilter()
accepted = []
for incident_number in range(47, 72):
    incident_id = f"incident-{incident_number}"
    if filter_index.add(incident_id):
        accepted.append(incident_id)
print("accepted=", len(accepted),
      "all-present=", all(filter_index.might_contain(incident_id)
                           for incident_id in accepted), sep="")
