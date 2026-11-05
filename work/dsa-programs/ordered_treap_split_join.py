from dataclasses import dataclass
from random import Random


@dataclass
class DepotNode:
    key: int
    priority: int
    left: "DepotNode | None" = None
    right: "DepotNode | None" = None
    size: int = 1


def count(node):
    return 0 if node is None else node.size


def repair(node):
    if node is not None:
        node.size = 1 + count(node.left) + count(node.right)
    return node


def split(node, boundary):
    """Return keys below boundary and keys at or above it."""
    if node is None:
        return None, None
    if node.key < boundary:
        node.right, upper = split(node.right, boundary)
        return repair(node), upper
    lower, node.left = split(node.left, boundary)
    return lower, repair(node)


def join(lower, upper):
    """Consume two trees whose key ranges do not overlap."""
    if lower is None or upper is None:
        return lower if upper is None else upper
    if lower.priority >= upper.priority:
        lower.right = join(lower.right, upper)
        return repair(lower)
    upper.left = join(lower, upper.left)
    return repair(upper)


def contains(node, key):
    while node is not None:
        if node.key == key:
            return True
        node = node.left if key < node.key else node.right
    return False


def insert(node, key, priority):
    if contains(node, key):
        return node
    lower, upper = split(node, key)
    return join(join(lower, DepotNode(key, priority)), upper)


def remove(node, key):
    lower, rest = split(node, key)
    middle, upper = split(rest, key + 1)
    return join(lower, upper), middle is not None


def select(node, position):
    if position < 0 or position >= count(node):
        raise IndexError(position)
    while node is not None:
        left_count = count(node.left)
        if position < left_count:
            node = node.left
        elif position == left_count:
            return node.key
        else:
            position -= left_count + 1
            node = node.right
    raise AssertionError("unreachable")


def ordered(node):
    return [] if node is None else ordered(node.left) + [node.key] + ordered(node.right)


priority_source = Random(947)
depot_root = None
for depot_key in (61, 19, 83, 47, 29):
    depot_root = insert(depot_root, depot_key, priority_source.getrandbits(48))
left_group, right_group = split(depot_root, 47)
print("split:", ordered(left_group), ordered(right_group))
depot_root = join(left_group, right_group)
depot_root, removed = remove(depot_root, 61)
print("rank two:", select(depot_root, 2), "removed:", removed)
print("ordered:", ordered(depot_root))
