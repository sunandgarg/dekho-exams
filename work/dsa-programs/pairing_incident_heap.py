import itertools


arrival_numbers = itertools.count()


class PairingNode:
    def __init__(self, priority, incident_id):
        self.key = (priority, next(arrival_numbers))
        self.incident_id = incident_id
        self.children = []


class PairingIncidentHeap:
    def __init__(self):
        self.root = None
        self.size = 0

    @staticmethod
    def _meld(left, right):
        if left is None:
            return right
        if right is None:
            return left
        if right.key < left.key:
            left, right = right, left
        left.children.append(right)
        return left

    def push(self, priority, incident_id):
        self.root = self._meld(self.root, PairingNode(priority, incident_id))
        self.size += 1

    def meld(self, other):
        if other is self:
            raise ValueError("cannot meld a heap into itself")
        self.root = self._meld(self.root, other.root)
        self.size += other.size
        other.root = None
        other.size = 0

    def pop(self):
        if self.root is None:
            raise IndexError("empty priority queue")
        removed = self.root
        children = removed.children
        paired = []
        for offset in range(0, len(children), 2):
            paired.append(self._meld(children[offset],
                                     children[offset + 1] if offset + 1 < len(children) else None))
        self.root = None
        for subtree in reversed(paired):
            self.root = self._meld(self.root, subtree)
        self.size -= 1
        return removed.key[0], removed.incident_id


east = PairingIncidentHeap()
west = PairingIncidentHeap()
east.push(47, "pump-47")
east.push(19, "valve-19")
west.push(19, "sensor-61")
west.push(61, "grid-83")
east.meld(west)
print("order=", [east.pop()[1] for _ in range(4)], "donor-size=", west.size, sep="")
