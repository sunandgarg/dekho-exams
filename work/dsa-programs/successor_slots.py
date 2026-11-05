class AvailableSlotIndex:
    def __init__(self, capacity):
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        self.capacity = capacity
        self.parent = list(range(capacity + 1))

    def _find(self, slot):
        trail = []
        while self.parent[slot] != slot:
            trail.append(slot)
            slot = self.parent[slot]
        for visited in trail:
            self.parent[visited] = slot
        return slot

    def next_available(self, start):
        if not 0 <= start <= self.capacity:
            raise IndexError(start)
        slot = self._find(start)
        return None if slot == self.capacity else slot

    def retire(self, slot):
        if not 0 <= slot < self.capacity:
            raise IndexError(slot)
        if self._find(slot) != slot:
            return False
        self.parent[slot] = self._find(slot + 1)
        return True

    def claim_next(self, start):
        slot = self.next_available(start)
        if slot is not None:
            self.retire(slot)
        return slot


loading_bays = AvailableSlotIndex(9)
for reserved_bay in (2, 3, 6):
    loading_bays.retire(reserved_bay)
print(loading_bays.claim_next(2), loading_bays.claim_next(2))
print(loading_bays.next_available(6), loading_bays.retire(3))
print(loading_bays.claim_next(8), loading_bays.claim_next(8))
