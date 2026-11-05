def euler_trail(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    outgoing, incoming = [[] for _ in range(vertex_count)], [0] * vertex_count
    for edge_id, pair in enumerate(edges):
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        source, target = pair
        outgoing[source].append((target, edge_id))
        incoming[target] += 1
    if not edges:
        return []
    differences = [len(outgoing[vertex]) - incoming[vertex] for vertex in range(vertex_count)]
    starts = [vertex for vertex, degree in enumerate(differences) if degree == 1]
    ends = [vertex for vertex, degree in enumerate(differences) if degree == -1]
    if any(abs(degree) > 1 for degree in differences) or not (len(starts) == len(ends) == 0 or len(starts) == len(ends) == 1):
        raise ValueError("trail degree pattern required")
    start = starts[0] if starts else next(vertex for vertex in range(vertex_count) if outgoing[vertex])
    for neighbors in outgoing:
        neighbors.reverse()
    stack, reversed_edges = [(start, None)], []
    while stack:
        vertex, edge_id = stack[-1]
        if outgoing[vertex]:
            target, next_id = outgoing[vertex].pop()
            stack.append((target, next_id))
        else:
            stack.pop()
            if edge_id is not None:
                reversed_edges.append(edge_id)
    if len(reversed_edges) != len(edges):
        raise ValueError("edge-bearing regions disconnected")
    return list(reversed(reversed_edges))

edges = [(0, 1), (1, 0), (0, 1), (1, 2)]
print("edge IDs:", euler_trail(3, edges))
try:
    euler_trail(4, [(0, 1), (1, 0), (2, 3), (3, 2)])
except ValueError:
    print("disconnected edges rejected")
