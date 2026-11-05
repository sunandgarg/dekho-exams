import itertools


arrival_numbers = itertools.count()


class BinomialNode:
    def __init__(self, priority, incident_id):
        self.key = (priority, next(arrival_numbers))
        self.incident_id = incident_id
        self.degree = 0
        self.children = []


class BinomialIncidentHeap:
    def __init__(self):
        self.roots = {}
        self.size = 0

    @staticmethod
    def _link(left, right):
        if right.key < left.key:
            left, right = right, left
        left.children.append(right)
        left.degree += 1
        return left

    def _add_tree(self, tree):
        while tree.degree in self.roots:
            tree = self._link(tree, self.roots.pop(tree.degree))
        self.roots[tree.degree] = tree

    def push(self, priority, incident_id):
        self._add_tree(BinomialNode(priority, incident_id))
        self.size += 1

    def meld(self, other):
        if other is self:
            raise ValueError("cannot meld a heap into itself")
        for tree in list(other.roots.values()):
            self._add_tree(tree)
        self.size += other.size
        other.roots.clear()
        other.size = 0

    def pop(self):
        if not self.roots:
            raise IndexError("empty priority queue")
        degree = min(self.roots, key=lambda level: self.roots[level].key)
        removed = self.roots.pop(degree)
        for subtree in removed.children:
            self._add_tree(subtree)
        self.size -= 1
        return removed.key[0], removed.incident_id


east = BinomialIncidentHeap()
west = BinomialIncidentHeap()
east.push(47, "pump-47")
east.push(19, "valve-19")
west.push(19, "sensor-61")
west.push(61, "grid-83")
east.meld(west)
print("order=", [east.pop()[1] for _ in range(4)], "donor-size=", west.size, sep="")
