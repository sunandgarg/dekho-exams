"""Fixed-capacity Robin Hood set with backward-shift deletion."""


class AssetSlotSet:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.slots: list[int | None] = [None] * capacity
        self.size = 0

    def _home(self, asset_id: int) -> int:
        return hash(asset_id) % self.capacity

    def _distance(self, asset_id: int, position: int) -> int:
        return (position - self._home(asset_id)) % self.capacity

    def _locate(self, asset_id: int) -> int | None:
        position = self._home(asset_id)
        distance = 0
        while distance < self.capacity:
            occupant = self.slots[position]
            if occupant is None or self._distance(occupant, position) < distance:
                return None
            if occupant == asset_id:
                return position
            position = (position + 1) % self.capacity
            distance += 1
        return None

    def contains(self, asset_id: int) -> bool:
        return self._locate(asset_id) is not None

    def insert(self, asset_id: int) -> bool:
        if self.contains(asset_id):
            return False
        if self.size == self.capacity:
            raise OverflowError("asset slots are full")
        position = self._home(asset_id)
        distance = 0
        incoming = asset_id
        while True:
            occupant = self.slots[position]
            if occupant is None:
                self.slots[position] = incoming
                self.size += 1
                return True
            occupant_distance = self._distance(occupant, position)
            if occupant_distance < distance:
                self.slots[position], incoming = incoming, occupant
                distance = occupant_distance
            position = (position + 1) % self.capacity
            distance += 1

    def remove(self, asset_id: int) -> bool:
        position = self._locate(asset_id)
        if position is None:
            return False
        next_position = (position + 1) % self.capacity
        while self.slots[next_position] is not None and self._distance(self.slots[next_position], next_position) > 0:
            self.slots[position] = self.slots[next_position]
            position = next_position
            next_position = (next_position + 1) % self.capacity
        self.slots[position] = None
        self.size -= 1
        return True


assets = AssetSlotSet(7)
for asset_id in (19, 26, 33, 47, 54):
    assets.insert(asset_id)
print(assets.contains(47))
print(assets.remove(26))
print(assets.contains(33))
print(sorted(asset_id for asset_id in assets.slots if asset_id is not None))
