"""Heavy-light decomposition with a Fenwick tree for node-weight path sums."""


class Fenwick:
    def __init__(self, values: list[int]):
        self.tree = [0] * (len(values) + 1)
        for position, value in enumerate(values):
            self.add(position, value)

    def add(self, position: int, difference: int) -> None:
        position += 1
        while position < len(self.tree):
            self.tree[position] += difference
            position += position & -position

    def prefix(self, stop: int) -> int:
        result = 0
        while stop:
            result += self.tree[stop]
            stop -= stop & -stop
        return result

    def between(self, start: int, stop: int) -> int:
        return self.prefix(stop) - self.prefix(start)


class DepotPathSums:
    def __init__(self, depot_ids: list[str], links: list[tuple[str, str]], weights: dict[str, int]):
        if len(depot_ids) != len(set(depot_ids)) or not depot_ids or set(weights) != set(depot_ids):
            raise ValueError("depots must be distinct, nonempty, and weighted")
        if len(links) != len(depot_ids) - 1:
            raise ValueError("a tree needs one fewer link than vertices")
        self.index = {depot_id: position for position, depot_id in enumerate(depot_ids)}
        count = len(depot_ids)
        neighbors = [[] for _ in depot_ids]
        for first, second in links:
            left, right = self.index[first], self.index[second]
            if left == right:
                raise ValueError("self-link")
            neighbors[left].append(right)
            neighbors[right].append(left)
        self.parent = [-1] * count
        self.depth = [0] * count
        traversal = [0]
        seen = {0}
        for current in traversal:
            for neighbor in neighbors[current]:
                if neighbor == self.parent[current]:
                    continue
                if neighbor in seen:
                    raise ValueError("links contain a cycle")
                seen.add(neighbor)
                self.parent[neighbor] = current
                self.depth[neighbor] = self.depth[current] + 1
                traversal.append(neighbor)
        if len(seen) != count:
            raise ValueError("links are disconnected")
        subtree_size = [1] * count
        heavy = [-1] * count
        for current in reversed(traversal):
            for neighbor in neighbors[current]:
                if self.parent[neighbor] == current:
                    subtree_size[current] += subtree_size[neighbor]
                    if heavy[current] < 0 or subtree_size[neighbor] > subtree_size[heavy[current]]:
                        heavy[current] = neighbor
        self.head = [0] * count
        self.position = [0] * count
        next_position = 0
        pending = [(0, 0)]
        while pending:
            current, chain_head = pending.pop()
            while current >= 0:
                self.head[current] = chain_head
                self.position[current] = next_position
                next_position += 1
                for neighbor in neighbors[current]:
                    if self.parent[neighbor] == current and neighbor != heavy[current]:
                        pending.append((neighbor, neighbor))
                current = heavy[current]
        self.weights = [weights[depot_id] for depot_id in depot_ids]
        flattened = [0] * count
        for vertex in range(count):
            flattened[self.position[vertex]] = self.weights[vertex]
        self.sums = Fenwick(flattened)

    def update(self, depot_id: str, weight: int) -> None:
        vertex = self.index[depot_id]
        self.sums.add(self.position[vertex], weight - self.weights[vertex])
        self.weights[vertex] = weight

    def path_sum(self, first: str, second: str) -> int:
        left, right = self.index[first], self.index[second]
        total = 0
        while self.head[left] != self.head[right]:
            if self.depth[self.head[left]] < self.depth[self.head[right]]:
                left, right = right, left
            chain_head = self.head[left]
            total += self.sums.between(self.position[chain_head], self.position[left] + 1)
            left = self.parent[chain_head]
        if self.depth[left] > self.depth[right]:
            left, right = right, left
        return total + self.sums.between(self.position[left], self.position[right] + 1)


depots = ["D-19", "D-26", "D-47", "D-52", "D-61", "D-83"]
links = [("D-19", "D-26"), ("D-19", "D-47"), ("D-26", "D-52"), ("D-26", "D-61"), ("D-47", "D-83")]
weights = {"D-19": 7, "D-26": 11, "D-47": 13, "D-52": 17, "D-61": 19, "D-83": 23}
path_index = DepotPathSums(depots, links, weights)
print(path_index.path_sum("D-52", "D-83"))
path_index.update("D-19", 29)
print(path_index.path_sum("D-52", "D-83"))
print(path_index.path_sum("D-61", "D-52"))
