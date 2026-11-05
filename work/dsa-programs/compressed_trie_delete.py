class PartNode:
    def __init__(self):
        self.terminal = False
        self.children = {}


part_root = PartNode()


def shared_length(first, second):
    length = 0
    while length < min(len(first), len(second)) and first[length] == second[length]:
        length += 1
    return length


def insert(part_code):
    if not part_code:
        raise ValueError("part code is empty")
    current = part_root
    suffix = part_code
    while suffix:
        edge = next((label for label in current.children if shared_length(label, suffix)), None)
        if edge is None:
            child = PartNode()
            child.terminal = True
            current.children[suffix] = child
            return
        width = shared_length(edge, suffix)
        if width < len(edge):
            old_child = current.children.pop(edge)
            branch = PartNode()
            branch.children[edge[width:]] = old_child
            current.children[edge[:width]] = branch
            edge = edge[:width]
        current = current.children[edge]
        suffix = suffix[width:]
    current.terminal = True


def locate(part_code):
    current = part_root
    suffix = part_code
    path = []
    while suffix:
        edge = next((label for label in current.children if suffix.startswith(label)), None)
        if edge is None:
            return None, []
        path.append((current, edge))
        current = current.children[edge]
        suffix = suffix[len(edge):]
    return current, path


def contains(part_code):
    current, _ = locate(part_code)
    return current is not None and current.terminal


def remove(part_code):
    current, path = locate(part_code)
    if current is None or not current.terminal:
        return False
    current.terminal = False
    for parent, edge in reversed(path):
        child = parent.children[edge]
        if child.terminal or len(child.children) > 1:
            break
        del parent.children[edge]
        if child.children:
            suffix, grandchild = next(iter(child.children.items()))
            parent.children[edge + suffix] = grandchild
    return True


for part_code in ("dock47", "dock52", "doll61", "dock"):
    insert(part_code)
print(remove("dock"), contains("dock"), contains("dock47"))
print(remove("dock52"), contains("dock52"), contains("doll61"))
