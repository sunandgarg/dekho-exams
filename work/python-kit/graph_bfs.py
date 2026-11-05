from collections import deque

def route_distances(graph, start):
    if type(start) is not int or not 1 <= len(graph) <= 1000 or not 0 <= start < len(graph):
        raise ValueError("graph bounds")
    if sum(map(len, graph)) > 10000 or any(type(vertex) is not int or not 0 <= vertex < len(graph) for row in graph for vertex in row):
        raise ValueError("edge bounds")
    distance = [-1] * len(graph)
    distance[start] = 0
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in graph[current]:
            if distance[neighbor] == -1:
                distance[neighbor] = distance[current] + 1
                pending.append(neighbor)
    return distance

print(route_distances([[1, 2], [3], [3], [], []], 0))
