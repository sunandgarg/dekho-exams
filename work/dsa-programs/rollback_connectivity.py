class RollbackConnectivity:
    def __init__(self, depot_ids):
        self.parent = {depot_id: depot_id for depot_id in depot_ids}
        self.size = {depot_id: 1 for depot_id in depot_ids}
        self.history = []

    def find(self, depot_id):
        current = depot_id
        while self.parent[current] != current:
            current = self.parent[current]
        return current

    def connected(self, first_depot, second_depot):
        return self.find(first_depot) == self.find(second_depot)

    def join(self, first_depot, second_depot):
        first_root = self.find(first_depot)
        second_root = self.find(second_depot)
        if first_root == second_root:
            return False
        if self.size[first_root] < self.size[second_root]:
            first_root, second_root = second_root, first_root
        self.history.append((second_root, first_root, self.size[first_root]))
        self.parent[second_root] = first_root
        self.size[first_root] += self.size[second_root]
        return True

    def checkpoint(self):
        return len(self.history)

    def rollback(self, checkpoint):
        if checkpoint < 0 or checkpoint > len(self.history):
            raise ValueError("checkpoint outside active history")
        while len(self.history) > checkpoint:
            child, root, old_size = self.history.pop()
            self.parent[child] = child
            self.size[root] = old_size


network = RollbackConnectivity(("D-19", "D-26", "D-47", "D-52"))
network.join("D-19", "D-26")
before_bridge = network.checkpoint()
network.join("D-26", "D-47")
print(network.connected("D-19", "D-47"))
network.rollback(before_bridge)
print(network.connected("D-19", "D-47"), network.connected("D-19", "D-26"))
