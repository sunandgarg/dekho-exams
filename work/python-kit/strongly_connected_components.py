def dependency_components(count, edges):
    if type(count) is not int or not 0 <= count <= 32 or len(edges) > 256:
        raise ValueError("graph budget rejected")
    forward, backward = [[] for _ in range(count)], [[] for _ in range(count)]
    for edge in edges:
        if not isinstance(edge, tuple) or len(edge) != 2 or any(type(node) is not int or not 0 <= node < count for node in edge):
            raise ValueError("edge rejected")
        source, target = edge
        forward[source].append(target); backward[target].append(source)
    seen = set(); finished = []
    def finish(node):
        seen.add(node)
        for neighbor in forward[node]:
            if neighbor not in seen: finish(neighbor)
        finished.append(node)
    for node in range(count):
        if node not in seen: finish(node)
    seen.clear(); components = []
    def collect(node, component):
        seen.add(node); component.append(node)
        for neighbor in backward[node]:
            if neighbor not in seen: collect(neighbor, component)
    for node in reversed(finished):
        if node not in seen:
            component = []; collect(node, component); components.append(sorted(component))
    return sorted(components)

print(dependency_components(6, [(0,1),(1,2),(2,0),(2,3),(3,4),(4,3)]))
print(dependency_components(2, [(0,1)]))
