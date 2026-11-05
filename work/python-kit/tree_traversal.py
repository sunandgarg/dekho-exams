def hierarchy_preorder(children, root):
    if type(root) is not int or root not in children or len(children) > 64:
        raise ValueError("root or hierarchy budget")
    if any(type(node) is not int or len(edges) > 64 or any(type(child) is not int or child not in children for child in edges)
           for node, edges in children.items()):
        raise ValueError("invalid child reference")
    pending, seen, ordered = [root], set(), []
    while pending:
        node = pending.pop()
        if node in seen:
            raise ValueError("reachable cycle or shared child")
        seen.add(node); ordered.append(node)
        pending.extend(reversed(children[node]))
    return ordered

print(hierarchy_preorder({0: [1, 2], 1: [3], 2: [], 3: []}, 0))
try:
    hierarchy_preorder({0: [1, 2], 1: [2], 2: []}, 0)
except ValueError:
    print("shared child rejected")
