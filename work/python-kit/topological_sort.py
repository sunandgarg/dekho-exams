import heapq

def dependency_order(graph):
    if len(graph) > 64 or any(type(node) is not str or len(edges) > 64 for node, edges in graph.items()):
        raise ValueError("graph budget")
    indegree = dict.fromkeys(graph, 0)
    for edges in graph.values():
        if len(edges) != len(set(edges)) or any(target not in graph for target in edges):
            raise ValueError("invalid dependency")
        for target in edges:
            indegree[target] += 1
    ready = [node for node, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        node = heapq.heappop(ready)
        ordered.append(node)
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)
    if len(ordered) != len(graph):
        raise ValueError("dependency cycle")
    return ordered

print(dependency_order({"import": ["validate"], "validate": ["publish"], "publish": []}))
try:
    dependency_order({"import": ["publish"], "publish": ["import"]})
except ValueError:
    print("cycle rejected")
