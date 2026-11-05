class ShipmentNeighborhoodSet:
    def __init__(self, capacity=31, neighborhood=5):
        if capacity < 2 or not 1 <= neighborhood <= capacity:
            raise ValueError("invalid capacity or neighborhood")
        self.capacity = capacity
        self.neighborhood = neighborhood
        self.slots = [None] * capacity
        self.count = 0

    def _home(self, shipment_id):
        return (shipment_id * 2654435761) % self.capacity

    def _distance(self, start, stop):
        return (stop - start) % self.capacity

    def contains(self, shipment_id):
        home = self._home(shipment_id)
        return any(self.slots[(home + step) % self.capacity] == shipment_id
                   for step in range(self.neighborhood))

    def add(self, shipment_id):
        if not isinstance(shipment_id, int):
            raise TypeError("shipment ID must be an integer")
        if self.contains(shipment_id):
            return True
        home = self._home(shipment_id)
        free = next(((home + step) % self.capacity for step in range(self.capacity)
                     if self.slots[(home + step) % self.capacity] is None), None)
        if free is None:
            return False
        while self._distance(home, free) >= self.neighborhood:
            moved = False
            for backward in range(self.neighborhood - 1, 0, -1):
                candidate = (free - backward) % self.capacity
                occupant = self.slots[candidate]
                if occupant is None:
                    continue
                if self._distance(self._home(occupant), free) < self.neighborhood:
                    self.slots[free] = occupant
                    self.slots[candidate] = None
                    free = candidate
                    moved = True
                    break
            if not moved:
                return False
        self.slots[free] = shipment_id
        self.count += 1
        return True

    def discard(self, shipment_id):
        home = self._home(shipment_id)
        for step in range(self.neighborhood):
            slot = (home + step) % self.capacity
            if self.slots[slot] == shipment_id:
                self.slots[slot] = None
                self.count -= 1
                return True
        return False


if __name__ == "__main__":
    registry = ShipmentNeighborhoodSet(capacity=31, neighborhood=5)
    for shipment_id in [47, 78, 109, 140, 171, 202]:
        print(shipment_id, registry.add(shipment_id))
    print(registry.contains(109), registry.discard(109), registry.contains(109))
    print(registry.count)
