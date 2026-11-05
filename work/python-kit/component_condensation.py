def condensation(vertex_count, edges):
    if type(vertex_count) is not int or not 0 <= vertex_count <= 32 or type(edges) is not list or len(edges) > 128:
        raise ValueError("bounded graph required")
    graph, reverse = [[] for _ in range(vertex_count)], [[] for _ in range(vertex_count)]
    for pair in edges:
        if type(pair) is not tuple or len(pair) != 2 or any(type(vertex) is not int or not 0 <= vertex < vertex_count for vertex in pair):
            raise ValueError("valid endpoints required")
        source, target = pair
        graph[source].append(target)
        reverse[target].append(source)
    seen, finished = set(), []
    def finish(vertex):
        seen.add(vertex)
        for target in graph[vertex]:
            if target not in seen:
                finish(target)
        finished.append(vertex)
    for vertex in range(vertex_count):
        if vertex not in seen:
            finish(vertex)
    seen.clear()
    components = []
    def collect(vertex, members):
        seen.add(vertex)
        members.append(vertex)
        for target in reverse[vertex]:
            if target not in seen:
                collect(target, members)
    for vertex in reversed(finished):
        if vertex not in seen:
            members = []
            collect(vertex, members)
            components.append(sorted(members))
    components.sort(key=lambda members: members[0])
    owner = {vertex: index for index, members in enumerate(components) for vertex in members}
    collapsed = sorted({(owner[source], owner[target]) for source, target in edges if owner[source] != owner[target]})
    return components, collapsed

print(condensation(5, [(0, 1), (1, 0), (1, 2), (2, 3), (3, 2), (3, 4)]))
