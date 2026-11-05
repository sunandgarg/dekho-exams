from collections import deque

def maximum_flow(vertex_count, edges, source, sink):
    if type(vertex_count) is not int or not 2 <= vertex_count <= 8 or type(source) is not int or type(sink) is not int or not 0 <= source < vertex_count or not 0 <= sink < vertex_count or source == sink or type(edges) is not list or len(edges) > 40:
        raise ValueError("network bounds")
    residual = [[0] * vertex_count for _ in range(vertex_count)]
    for edge in edges:
        if type(edge) is not tuple or len(edge) != 3 or any(type(value) is not int for value in edge):
            raise ValueError("integer edge")
        start, end, capacity = edge
        if not 0 <= start < vertex_count or not 0 <= end < vertex_count or not 0 <= capacity <= 1000 or start == end:
            raise ValueError("edge fields")
        residual[start][end] += capacity
    total = 0
    while True:
        parent = {source: None}
        pending = deque([source])
        while pending and sink not in parent:
            current = pending.popleft()
            for neighbor, capacity in enumerate(residual[current]):
                if capacity > 0 and neighbor not in parent:
                    parent[neighbor] = current
                    pending.append(neighbor)
        if sink not in parent:
            return total
        bottleneck = float("inf")
        node = sink
        while node != source:
            previous = parent[node]
            bottleneck = min(bottleneck, residual[previous][node])
            node = previous
        node = sink
        while node != source:
            previous = parent[node]
            residual[previous][node] -= bottleneck
            residual[node][previous] += bottleneck
            node = previous
        total += bottleneck

network = [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 3)]
print(maximum_flow(4, network, 0, 3))
