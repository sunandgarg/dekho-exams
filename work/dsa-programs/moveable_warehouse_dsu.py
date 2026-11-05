class MoveableWarehouseGroups:
    def __init__(self, shipment_count):
        if shipment_count < 0:
            raise ValueError("negative shipment count")
        self.shipment_count = shipment_count
        self.node_for = list(range(shipment_count))
        self.parent = list(range(shipment_count))
        self.size = [1] * shipment_count
        self.total = list(range(shipment_count))

    def _check(self, shipment):
        if not 0 <= shipment < self.shipment_count:
            raise IndexError(shipment)

    def _root(self, node):
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def group(self, shipment):
        self._check(shipment)
        root = self._root(self.node_for[shipment])
        return self.size[root], self.total[root]

    def together(self, first, second):
        self._check(first)
        self._check(second)
        return self._root(self.node_for[first]) == self._root(self.node_for[second])

    def merge(self, first, second):
        self._check(first)
        self._check(second)
        first_root = self._root(self.node_for[first])
        second_root = self._root(self.node_for[second])
        if first_root == second_root:
            return False
        if self.size[first_root] < self.size[second_root]:
            first_root, second_root = second_root, first_root
        self.parent[second_root] = first_root
        self.size[first_root] += self.size[second_root]
        self.total[first_root] += self.total[second_root]
        return True

    def move(self, shipment, destination):
        self._check(shipment)
        self._check(destination)
        old_root = self._root(self.node_for[shipment])
        target_root = self._root(self.node_for[destination])
        if old_root == target_root:
            return False
        self.size[old_root] -= 1
        self.total[old_root] -= shipment
        new_node = len(self.parent)
        self.parent.append(target_root)
        self.size.append(1)
        self.total.append(shipment)
        self.node_for[shipment] = new_node
        self.size[target_root] += 1
        self.total[target_root] += shipment
        return True


warehouse_groups = MoveableWarehouseGroups(7)
warehouse_groups.merge(1, 3)
warehouse_groups.merge(3, 5)
warehouse_groups.merge(2, 4)
print("before move:", warehouse_groups.group(1), warehouse_groups.group(2))
warehouse_groups.move(3, 4)
print("after move:", warehouse_groups.group(1), warehouse_groups.group(2))
print("old link:", warehouse_groups.together(1, 3))
