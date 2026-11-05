class DepotEulerAncestorIndex:
    def __init__(self, depot_count, roads, root=0):
        if depot_count < 1 or len(roads) != depot_count - 1 or not 0 <= root < depot_count:
            raise ValueError("expected a nonempty rooted tree")
        adjacent = [[] for _ in range(depot_count)]
        for first, second in roads:
            if not (0 <= first < depot_count and 0 <= second < depot_count) or first == second:
                raise ValueError("invalid tree edge")
            adjacent[first].append(second)
            adjacent[second].append(first)
        self.first = {}
        self.euler = []
        self.depth_at = []
        self.node_depth = {}

        def visit(node, parent, depth):
            if node in self.first:
                raise ValueError("cycle detected")
            self.first[node] = len(self.euler)
            self.node_depth[node] = depth
            self.euler.append(node)
            self.depth_at.append(depth)
            for child in adjacent[node]:
                if child == parent:
                    continue
                visit(child, node, depth + 1)
                self.euler.append(node)
                self.depth_at.append(depth)

        visit(root, -1, 0)
        if len(self.first) != depot_count:
            raise ValueError("disconnected depot network")
        self.sparse = [list(range(len(self.euler)))]
        span = 2
        while span <= len(self.euler):
            previous = self.sparse[-1]
            half = span // 2
            self.sparse.append([min(previous[start], previous[start + half],
                                    key=lambda index: (self.depth_at[index], index))
                                for start in range(len(self.euler) - span + 1)])
            span *= 2

    def lowest_common_depot(self, first_id, second_id):
        left, right = sorted((self.first[first_id], self.first[second_id]))
        power = (right - left + 1).bit_length() - 1
        width = 1 << power
        first_index = self.sparse[power][left]
        second_index = self.sparse[power][right - width + 1]
        best = min(first_index, second_index, key=lambda index: (self.depth_at[index], index))
        return self.euler[best]

    def road_distance(self, first_id, second_id):
        ancestor = self.lowest_common_depot(first_id, second_id)
        return self.node_depth[first_id] + self.node_depth[second_id] - 2 * self.node_depth[ancestor]


if __name__ == "__main__":
    network = DepotEulerAncestorIndex(7, [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (5, 6)])
    print("common depot 2,6:", network.lowest_common_depot(2, 6))
    print("road distance 2,6:", network.road_distance(2, 6))
    print("Euler entries:", len(network.euler))
