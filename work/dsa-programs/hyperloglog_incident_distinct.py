import hashlib
import math


class DistinctIncidentEstimate:
    def __init__(self, precision=6):
        if not 4 <= precision <= 16:
            raise ValueError("precision must be between 4 and 16")
        self.precision = precision
        self.registers = [0] * (1 << precision)

    def add(self, incident_id):
        digest = hashlib.sha256(incident_id.encode("utf-8")).digest()
        fingerprint = int.from_bytes(digest[:8], "big")
        remaining_bits = 64 - self.precision
        bucket = fingerprint >> remaining_bits
        suffix = fingerprint & ((1 << remaining_bits) - 1)
        rank = remaining_bits - suffix.bit_length() + 1 if suffix else remaining_bits + 1
        self.registers[bucket] = max(self.registers[bucket], rank)

    def merge(self, other):
        if self.precision != other.precision:
            raise ValueError("precision mismatch")
        self.registers = [max(left, right) for left, right in zip(self.registers, other.registers)]

    def estimate(self):
        register_count = len(self.registers)
        alpha = {16: 0.673, 32: 0.697, 64: 0.709}.get(
            register_count, 0.7213 / (1 + 1.079 / register_count))
        harmonic = sum(2.0 ** -rank for rank in self.registers)
        raw = alpha * register_count * register_count / harmonic
        empty = self.registers.count(0)
        if raw <= 2.5 * register_count and empty:
            return register_count * math.log(register_count / empty)
        return raw


east = DistinctIncidentEstimate(8)
west = DistinctIncidentEstimate(8)
for incident_number in range(47, 147):
    east.add(f"incident-{incident_number}")
for incident_number in range(97, 197):
    west.add(f"incident-{incident_number}")
east.merge(west)
print("estimate=", round(east.estimate()), "registers=", len(east.registers), sep="")
