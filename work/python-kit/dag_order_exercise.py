def valid_order(nodes, edges, proposed):
    if type(nodes) is not list or len(nodes) > 30 or any(type(node) is not str or not node for node in nodes) or len(set(nodes)) != len(nodes):
        raise ValueError("node set")
    if type(edges) is not list or len(edges) > 100 or any(type(edge) is not tuple or len(edge) != 2 or edge[0] not in nodes or edge[1] not in nodes for edge in edges):
        raise ValueError("edge set")
    if type(proposed) is not list or len(proposed) != len(nodes) or any(type(node) is not str for node in proposed) or set(proposed) != set(nodes):
        return False
    position = {node: index for index, node in enumerate(proposed)}
    return all(position[source] < position[target] for source, target in edges)

steps = ["read", "validate", "publish"]
edges = [("read", "validate"), ("validate", "publish")]
print(valid_order(steps, edges, ["read", "validate", "publish"]))
print(valid_order(steps, edges, ["validate", "read", "publish"]))
