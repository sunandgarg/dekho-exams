class DepotBlockCutIndex:
    def __init__(self, vertex_count, roads):
        if vertex_count < 0:
            raise ValueError("negative vertex count")
        self.vertex_count = vertex_count
        adjacency = [[] for _ in range(vertex_count)]
        seen = set()
        for source, target in roads:
            if not (0 <= source < vertex_count and 0 <= target < vertex_count) or source == target:
                raise ValueError("road endpoints must be distinct known vertices")
            edge = (min(source, target), max(source, target))
            if edge in seen:
                raise ValueError("parallel roads are outside this simple-graph model")
            seen.add(edge)
            adjacency[source].append(target)
            adjacency[target].append(source)
        for neighbors in adjacency:
            neighbors.sort()
        discovery = [-1] * vertex_count
        low = [0] * vertex_count
        edge_stack = []
        blocks = []
        articulations = set()
        clock = 0

        def walk(vertex, parent):
            nonlocal clock
            discovery[vertex] = low[vertex] = clock
            clock += 1
            child_count = 0
            for neighbor in adjacency[vertex]:
                if discovery[neighbor] == -1:
                    child_count += 1
                    edge_stack.append((vertex, neighbor))
                    walk(neighbor, vertex)
                    low[vertex] = min(low[vertex], low[neighbor])
                    if low[neighbor] >= discovery[vertex]:
                        if parent != -1 or child_count > 1:
                            articulations.add(vertex)
                        block = set()
                        while edge_stack:
                            edge_source, edge_target = edge_stack.pop()
                            block.update((edge_source, edge_target))
                            if (edge_source, edge_target) == (vertex, neighbor):
                                break
                        blocks.append(frozenset(block))
                elif neighbor != parent and discovery[neighbor] < discovery[vertex]:
                    low[vertex] = min(low[vertex], discovery[neighbor])
                    edge_stack.append((vertex, neighbor))

        for start in range(vertex_count):
            if discovery[start] == -1:
                walk(start, -1)
                if not adjacency[start]:
                    blocks.append(frozenset((start,)))
        self.blocks = sorted(blocks, key=lambda block: (min(block), len(block), sorted(block)))
        self.articulations = articulations
        self.block_neighbors = {
            articulation: [index for index, block in enumerate(self.blocks) if articulation in block]
            for articulation in sorted(articulations)
        }

    def blocks_for(self, vertex):
        if not 0 <= vertex < self.vertex_count:
            raise IndexError(vertex)
        return [index for index, block in enumerate(self.blocks) if vertex in block]


depot_index = DepotBlockCutIndex(
    8, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3), (5, 6)]
)
print("blocks:", [sorted(block) for block in depot_index.blocks])
print("cut depots:", sorted(depot_index.articulations))
print("depot five blocks:", depot_index.blocks_for(5))
