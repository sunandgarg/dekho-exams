class MarkedDepotCentroids:
    def __init__(self, depot_count, roads):
        if depot_count < 1 or len(roads) != depot_count - 1:
            raise ValueError("roads must form a nonempty tree")
        self.adjacent = [[] for _ in range(depot_count)]
        for first, second in roads:
            if not (0 <= first < depot_count and 0 <= second < depot_count) or first == second:
                raise ValueError("invalid tree edge")
            self.adjacent[first].append(second)
            self.adjacent[second].append(first)
        seen = {0}
        pending = [0]
        while pending:
            for neighbor in self.adjacent[pending.pop()]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
        if len(seen) != depot_count:
            raise ValueError("roads must connect every depot")
        self.blocked = [False] * depot_count
        self.paths = [[] for _ in range(depot_count)]
        self.best_marked = [float("inf")] * depot_count
        self.marked = set()
        self._decompose(0)

    def _decompose(self, start):
        parent = {start: -1}
        order = [start]
        for current in order:
            for neighbor in self.adjacent[current]:
                if neighbor != parent[current] and not self.blocked[neighbor]:
                    parent[neighbor] = current
                    order.append(neighbor)
        sizes = {node: 1 for node in order}
        for node in reversed(order):
            if parent[node] != -1:
                sizes[parent[node]] += sizes[node]
        total = len(order)
        centroid = min(order, key=lambda node: (
            max([total - sizes[node]] + [sizes[neighbor] for neighbor in self.adjacent[node]
                                          if not self.blocked[neighbor] and parent.get(neighbor) == node]), node))
        pending = [(centroid, -1, 0)]
        while pending:
            node, previous, distance = pending.pop()
            self.paths[node].append((centroid, distance))
            for neighbor in self.adjacent[node]:
                if neighbor != previous and not self.blocked[neighbor]:
                    pending.append((neighbor, node, distance + 1))
        self.blocked[centroid] = True
        for neighbor in self.adjacent[centroid]:
            if not self.blocked[neighbor]:
                self._decompose(neighbor)

    def mark(self, depot_id):
        if depot_id in self.marked:
            return False
        self.marked.add(depot_id)
        for centroid, distance in self.paths[depot_id]:
            self.best_marked[centroid] = min(self.best_marked[centroid], distance)
        return True

    def nearest_marked_distance(self, depot_id):
        result = min((distance + self.best_marked[centroid]
                      for centroid, distance in self.paths[depot_id]), default=float("inf"))
        return None if result == float("inf") else result


if __name__ == "__main__":
    network = MarkedDepotCentroids(7, [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (5, 6)])
    print("before marking:", network.nearest_marked_distance(2))
    network.mark(4)
    print("from 2:", network.nearest_marked_distance(2))
    network.mark(6)
    print("from 5:", network.nearest_marked_distance(5))
