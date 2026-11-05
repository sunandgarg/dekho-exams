def articulation_points(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    adjacency = [[] for _ in range(vertex_count)]
    for edge_id, pair in enumerate(edges):
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        left, right = pair
        adjacency[left].append((right, edge_id))
        adjacency[right].append((left, edge_id))
    discovered, low = [-1] * vertex_count, [0] * vertex_count
    clock, separating = 0, set()
    def visit(vertex, incoming):
        nonlocal clock
        discovered[vertex] = low[vertex] = clock
        clock += 1
        children = 0
        for neighbor, edge_id in adjacency[vertex]:
            if edge_id == incoming:
                continue
            if discovered[neighbor] == -1:
                children += 1
                visit(neighbor, edge_id)
                low[vertex] = min(low[vertex], low[neighbor])
                if incoming is not None and low[neighbor] >= discovered[vertex]:
                    separating.add(vertex)
            else:
                low[vertex] = min(low[vertex], discovered[neighbor])
        if incoming is None and children > 1:
            separating.add(vertex)
    for vertex in range(vertex_count):
        if discovered[vertex] == -1:
            visit(vertex, None)
    return sorted(separating)

print("separating:", articulation_points(5, [(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (1, 3)]))
print("cycle:", articulation_points(3, [(0, 1), (1, 2), (2, 0)]))
