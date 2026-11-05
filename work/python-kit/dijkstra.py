import heapq

def route_costs(graph, source):
    if type(source) is not int or source not in graph or len(graph) > 64:
        raise ValueError("source or graph budget")
    for node, edges in graph.items():
        if type(node) is not int or len(edges) > 64:
            raise ValueError("node budget")
        for target, cost in edges:
            if type(target) is not int or target not in graph or type(cost) is not int or not 0 <= cost <= 1000:
                raise ValueError("nonnegative bounded edges required")
    distances = dict.fromkeys(graph, None)
    distances[source] = 0
    pending = [(0, source)]
    while pending:
        distance, node = heapq.heappop(pending)
        if distance != distances[node]:
            continue
        for target, cost in graph[node]:
            candidate = distance + cost
            if distances[target] is None or candidate < distances[target]:
                distances[target] = candidate
                heapq.heappush(pending, (candidate, target))
    return distances

print(route_costs({0: [(1, 9), (2, 2)], 1: [], 2: [(1, 3)], 3: []}, 0))
try:
    route_costs({0: [(1, -1)], 1: []}, 0)
except ValueError:
    print("negative edge rejected")
