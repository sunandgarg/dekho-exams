from collections import deque

def transfer_cost(graph, start, goal):
    if type(graph) is not dict or not 1 <= len(graph) <= 30 or start not in graph or goal not in graph:
        raise ValueError("graph boundary")
    if any(type(edges) is not list or len(edges) > 30 or any(type(edge) is not tuple or len(edge) != 2 or edge[0] not in graph or type(edge[1]) is not int or edge[1] not in (0, 1) for edge in edges) for edges in graph.values()):
        raise ValueError("binary weights")
    distances = {start: 0}
    queue = deque([(start, 0)])
    while queue:
        station, cost = queue.popleft()
        if cost != distances[station]:
            continue
        for neighbor, weight in graph[station]:
            next_cost = cost + weight
            if next_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = next_cost
                if weight == 0:
                    queue.appendleft((neighbor, next_cost))
                else:
                    queue.append((neighbor, next_cost))
    return distances.get(goal)

routes = {"A": [("B", 1), ("C", 0)], "B": [("D", 0)],
          "C": [("B", 0), ("D", 1)], "D": []}
print(transfer_cost(routes, "A", "D"))
try:
    transfer_cost({"A": [("B", 2)], "B": []}, "A", "B")
except ValueError:
    print("weight rejected")
