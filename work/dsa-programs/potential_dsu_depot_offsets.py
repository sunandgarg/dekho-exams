class DepotOffsetConstraints:
    def __init__(self, count):
        self.parent = list(range(count))
        self.size = [1] * count
        self.offset = [0] * count  # value[node] - value[parent]

    def find(self, depot):
        if self.parent[depot] == depot:
            return depot, 0
        previous = self.parent[depot]
        root, parent_offset = self.find(previous)
        self.offset[depot] += parent_offset
        self.parent[depot] = root
        return root, self.offset[depot]

    def constrain(self, first, second, difference):
        """Require value[second] - value[first] == difference."""
        first_root, first_offset = self.find(first)
        second_root, second_offset = self.find(second)
        if first_root == second_root:
            return second_offset - first_offset == difference
        if self.size[first_root] >= self.size[second_root]:
            self.parent[second_root] = first_root
            self.offset[second_root] = difference + first_offset - second_offset
            self.size[first_root] += self.size[second_root]
        else:
            self.parent[first_root] = second_root
            self.offset[first_root] = second_offset - first_offset - difference
            self.size[second_root] += self.size[first_root]
        return True

    def difference(self, first, second):
        first_root, first_offset = self.find(first)
        second_root, second_offset = self.find(second)
        return None if first_root != second_root else second_offset - first_offset


network = DepotOffsetConstraints(5)
print(network.constrain(0, 1, 47), network.constrain(1, 2, -19))
print(network.difference(0, 2), network.constrain(0, 2, 29))
