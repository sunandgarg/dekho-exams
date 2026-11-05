def bridge_links(count, edges):
    if type(count) is not int or not 0 <= count <= 32 or len(edges) > 256:
        raise ValueError("graph budget rejected")
    adjacency = [[] for _ in range(count)]
    for number, edge in enumerate(edges):
        if not isinstance(edge, tuple) or len(edge) != 2 or any(type(node) is not int or not 0 <= node < count for node in edge):
            raise ValueError("edge rejected")
        first, second = edge
        adjacency[first].append((second, number)); adjacency[second].append((first, number))
    discovery = [-1] * count; earliest = [0] * count; clock = 0; result = []
    def visit(node, parent_edge):
        nonlocal clock
        discovery[node] = earliest[node] = clock; clock += 1
        for neighbor, edge_id in adjacency[node]:
            if edge_id == parent_edge: continue
            if discovery[neighbor] < 0:
                visit(neighbor, edge_id)
                earliest[node] = min(earliest[node], earliest[neighbor])
                if earliest[neighbor] > discovery[node]: result.append(edge_id)
            else:
                earliest[node] = min(earliest[node], discovery[neighbor])
    for node in range(count):
        if discovery[node] < 0: visit(node, -1)
    return sorted(result)

print("parallel-safe bridges:", bridge_links(4, [(0,1),(0,1),(1,2),(2,3),(3,2)]))
print("cycle bridges:", bridge_links(3, [(0,1),(1,2),(2,0)]))
