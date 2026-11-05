def network_forest(count, edges):
    if type(count) is not int or not 1 <= count <= 32 or len(edges) > 256:
        raise ValueError("network budget exceeded")
    for start, end, weight in edges:
        if any(type(value) is not int for value in (start, end, weight)):
            raise ValueError("integer edge required")
        if not 0 <= start < count or not 0 <= end < count or abs(weight) > 1000000:
            raise ValueError("invalid edge")
    parents = list(range(count))
    sizes = [1] * count
    def find(site):
        while parents[site] != site:
            parents[site] = parents[parents[site]]
            site = parents[site]
        return site
    total = 0
    components = count
    for start, end, weight in sorted(edges, key=lambda edge: edge[2]):
        first, second = find(start), find(end)
        if first == second:
            continue
        if sizes[first] < sizes[second]:
            first, second = second, first
        parents[second] = first
        sizes[first] += sizes[second]
        total += weight
        components -= 1
    return total, components

print(network_forest(4, [(0, 1, 4), (1, 2, 2), (0, 2, 3)]))
print(network_forest(2, [(0, 0, -5), (0, 1, -2)]))
