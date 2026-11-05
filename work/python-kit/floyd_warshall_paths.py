def all_pairs(vertex_count, edges):
    if type(vertex_count) is not int or not 1 <= vertex_count <= 12 or type(edges) is not list or len(edges) > 100:
        raise ValueError("graph bounds")
    infinity = float("inf")
    distance = [[0 if row == col else infinity for col in range(vertex_count)] for row in range(vertex_count)]
    for edge in edges:
        if type(edge) is not tuple or len(edge) != 3:
            raise ValueError("edge tuple")
        start, end, cost = edge
        if any(type(value) is not int for value in edge) or not 0 <= start < vertex_count or not 0 <= end < vertex_count or not -10 <= cost <= 10:
            raise ValueError("edge fields")
        distance[start][end] = min(distance[start][end], cost)
    for middle in range(vertex_count):
        for start in range(vertex_count):
            for end in range(vertex_count):
                distance[start][end] = min(distance[start][end], distance[start][middle] + distance[middle][end])
    if any(distance[index][index] < 0 for index in range(vertex_count)):
        raise ValueError("negative cycle")
    return [[None if value == infinity else value for value in row] for row in distance]

matrix = all_pairs(3, [(0, 1, 5), (1, 2, 2), (0, 2, 9)])
print(matrix[0], matrix[2][0])
try:
    all_pairs(2, [(0, 1, -2), (1, 0, 1)])
except ValueError:
    print("negative cycle rejected")
