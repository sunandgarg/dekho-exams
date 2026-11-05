"""Exact online connectivity with adjacency sets and a fresh search per question."""

from collections import deque


class DepotNetwork:
    def __init__(self, depot_ids):
        depot_ids = tuple(depot_ids)
        if len(set(depot_ids)) != len(depot_ids):
            raise ValueError("duplicate depot")
        self.neighbors = {depot_id: set() for depot_id in depot_ids}

    def _check(self, first, second):
        if first not in self.neighbors or second not in self.neighbors:
            raise KeyError("unknown depot")
        if first == second:
            raise ValueError("self-edge")

    def connect(self, first, second):
        self._check(first, second)
        if second in self.neighbors[first]:
            raise ValueError("edge already active")
        self.neighbors[first].add(second)
        self.neighbors[second].add(first)

    def disconnect(self, first, second):
        self._check(first, second)
        if second not in self.neighbors[first]:
            raise ValueError("edge is absent")
        self.neighbors[first].remove(second)
        self.neighbors[second].remove(first)

    def connected(self, source, destination):
        if source not in self.neighbors or destination not in self.neighbors:
            raise KeyError("unknown depot")
        visited = {source}
        pending = deque([source])
        while pending:
            depot = pending.popleft()
            if depot == destination:
                return True
            for adjacent in self.neighbors[depot]:
                if adjacent not in visited:
                    visited.add(adjacent)
                    pending.append(adjacent)
        return False


network = DepotNetwork(("D-19", "D-26", "D-47"))
network.connect("D-19", "D-26")
print(network.connected("D-19", "D-47"))
network.connect("D-26", "D-47")
print(network.connected("D-19", "D-47"))
network.disconnect("D-26", "D-47")
print(network.connected("D-19", "D-47"))
