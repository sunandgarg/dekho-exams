def signed_routes(count, edges, source):
    if type(count) is not int or not 1 <= count <= 32:
        raise ValueError("node budget exceeded")
    if type(source) is not int or not 0 <= source < count or len(edges) > 512:
        raise ValueError("invalid source or edge budget")
    for start, end, weight in edges:
        if any(type(value) is not int for value in (start, end, weight)):
            raise ValueError("integer edges required")
        if not 0 <= start < count or not 0 <= end < count or abs(weight) > 1000000:
            raise ValueError("invalid edge")
    costs = [None] * count
    costs[source] = 0
    for _ in range(count - 1):
        changed = False
        for start, end, weight in edges:
            if costs[start] is not None:
                candidate = costs[start] + weight
                if costs[end] is None or candidate < costs[end]:
                    costs[end] = candidate
                    changed = True
        if not changed:
            break
    for start, end, weight in edges:
        if costs[start] is not None and (costs[end] is None or costs[start] + weight < costs[end]):
            raise ValueError("reachable negative cycle")
    return costs

print(signed_routes(4, [(0, 1, 5), (1, 2, -2), (0, 2, 8)], 0))
try:
    signed_routes(3, [(0, 1, 1), (1, 2, -2), (2, 1, 1)], 0)
except ValueError:
    print("reachable negative cycle rejected")
