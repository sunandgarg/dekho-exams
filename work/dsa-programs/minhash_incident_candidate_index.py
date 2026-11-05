import hashlib
from collections import defaultdict


def token_hash(token, permutation):
    payload = str(permutation).encode() + b"\0" + token.encode("utf-8")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "big")


def signature(tokens, width=24):
    if not tokens:
        raise ValueError("empty token set has no signature")
    return tuple(min(token_hash(token, number) for token in tokens) for number in range(width))


class IncidentCandidateIndex:
    def __init__(self, bands=6, rows_per_band=4):
        if bands <= 0 or rows_per_band <= 0:
            raise ValueError("positive band dimensions required")
        self.bands = bands
        self.rows_per_band = rows_per_band
        self.records = {}
        self.buckets = defaultdict(set)

    def _keys(self, sketch):
        for band in range(self.bands):
            start = band * self.rows_per_band
            yield band, sketch[start:start + self.rows_per_band]

    def add(self, incident_id, tokens):
        if incident_id in self.records:
            raise ValueError("duplicate incident ID")
        token_set = frozenset(tokens)
        sketch = signature(token_set, self.bands * self.rows_per_band)
        self.records[incident_id] = (token_set, sketch)
        for key in self._keys(sketch):
            self.buckets[key].add(incident_id)

    def query(self, tokens, minimum_similarity):
        if not 0 <= minimum_similarity <= 1:
            raise ValueError("similarity outside [0,1]")
        token_set = frozenset(tokens)
        sketch = signature(token_set, self.bands * self.rows_per_band)
        candidates = set()
        for key in self._keys(sketch):
            candidates.update(self.buckets[key])
        matches = []
        for incident_id in candidates:
            stored_tokens, _ = self.records[incident_id]
            similarity = len(token_set & stored_tokens) / len(token_set | stored_tokens)
            if similarity >= minimum_similarity:
                matches.append((incident_id, round(similarity, 3)))
        return sorted(matches)


incident_index = IncidentCandidateIndex()
incident_index.add("I-19", {"dock", "scanner", "offline", "night"})
incident_index.add("I-47", {"dock", "scanner", "offline", "night", "retry"})
incident_index.add("I-83", {"invoice", "paid", "review"})
print("near matches:", incident_index.query({"dock", "scanner", "offline", "night"}, 0.75))
