class BottleneckRouteTree:
    def __init__(self, depot_count, roads):
        if depot_count < 0:
            raise ValueError("negative depot count")
        self.depot_count = depot_count
        dsu_parent = list(range(depot_count))
        dsu_size = [1] * depot_count
        tree_root = list(range(depot_count))
        self.weight = [None] * depot_count
        self.parent = [-1] * depot_count
        children = [[] for _ in range(depot_count)]

        def find(vertex):
            while dsu_parent[vertex] != vertex:
                dsu_parent[vertex] = dsu_parent[dsu_parent[vertex]]
                vertex = dsu_parent[vertex]
            return vertex

        for weight, source, target in sorted(roads):
            if not (0 <= source < depot_count and 0 <= target < depot_count) or weight < 0:
                raise ValueError("roads need known vertices and nonnegative weights")
            first, second = find(source), find(target)
            if first == second:
                continue
            merge_node = len(self.weight)
            self.weight.append(weight)
            self.parent.append(-1)
            children.append([tree_root[first], tree_root[second]])
            self.parent[tree_root[first]] = merge_node
            self.parent[tree_root[second]] = merge_node
            if dsu_size[first] < dsu_size[second]:
                first, second = second, first
            dsu_parent[second] = first
            dsu_size[first] += dsu_size[second]
            tree_root[first] = merge_node
        self.component = [find(vertex) for vertex in range(depot_count)]
        node_count = len(self.weight)
        self.depth = [0] * node_count
        roots = [node for node, parent in enumerate(self.parent) if parent == -1]
        for root in roots:
            pending = [root]
            while pending:
                node = pending.pop()
                for child in children[node]:
                    self.depth[child] = self.depth[node] + 1
                    pending.append(child)
        levels = max(1, node_count.bit_length())
        self.up = [self.parent[:]]
        for _ in range(1, levels):
            previous = self.up[-1]
            self.up.append([-1 if ancestor == -1 else previous[ancestor] for ancestor in previous])

    def bottleneck(self, source, target):
        if not (0 <= source < self.depot_count and 0 <= target < self.depot_count):
            raise IndexError("unknown depot")
        if source == target:
            return 0
        if self.component[source] != self.component[target]:
            return None
        if self.depth[source] < self.depth[target]:
            source, target = target, source
        difference = self.depth[source] - self.depth[target]
        for level in range(len(self.up)):
            if difference & (1 << level):
                source = self.up[level][source]
        if source != target:
            for level in range(len(self.up) - 1, -1, -1):
                if self.up[level][source] != self.up[level][target]:
                    source = self.up[level][source]
                    target = self.up[level][target]
            source = self.parent[source]
        return self.weight[source]


route_tree = BottleneckRouteTree(6, [(19, 0, 1), (47, 1, 2), (29, 0, 2), (61, 2, 3), (83, 3, 4)])
print("zero to two:", route_tree.bottleneck(0, 2))
print("zero to four:", route_tree.bottleneck(0, 4))
print("zero to five:", route_tree.bottleneck(0, 5))
