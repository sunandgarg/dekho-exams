"""Immutable randomized treap with version roots and structural sharing."""

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class IndexNode:
    asset_id: int
    owner: str
    priority: int
    left: "IndexNode | None" = None
    right: "IndexNode | None" = None


def find(root, asset_id):
    while root is not None:
        if asset_id == root.asset_id:
            return root.owner
        root = root.left if asset_id < root.asset_id else root.right
    return None


def split(root, asset_id):
    """Return keys below asset_id and keys at or above it."""
    if root is None:
        return None, None
    if root.asset_id < asset_id:
        left_of_cut, right_of_cut = split(root.right, asset_id)
        return IndexNode(root.asset_id, root.owner, root.priority, root.left, left_of_cut), right_of_cut
    left_of_cut, right_of_cut = split(root.left, asset_id)
    return left_of_cut, IndexNode(root.asset_id, root.owner, root.priority, right_of_cut, root.right)


def merge(lower, upper):
    if lower is None:
        return upper
    if upper is None:
        return lower
    if lower.priority < upper.priority:
        return IndexNode(lower.asset_id, lower.owner, lower.priority, lower.left, merge(lower.right, upper))
    return IndexNode(upper.asset_id, upper.owner, upper.priority, merge(lower, upper.left), upper.right)


def put(root, asset_id, owner, priority):
    if find(root, asset_id) is not None:
        raise ValueError("duplicate asset")
    lower, upper = split(root, asset_id)
    return merge(merge(lower, IndexNode(asset_id, owner, priority)), upper)


def remove(root, asset_id):
    if root is None:
        raise KeyError(asset_id)
    if asset_id == root.asset_id:
        return merge(root.left, root.right)
    if asset_id < root.asset_id:
        return IndexNode(root.asset_id, root.owner, root.priority, remove(root.left, asset_id), root.right)
    return IndexNode(root.asset_id, root.owner, root.priority, root.left, remove(root.right, asset_id))


def ordered(root):
    if root is None:
        return []
    return ordered(root.left) + [(root.asset_id, root.owner)] + ordered(root.right)


priority_source = Random(4726)
version_zero = None
version_one = put(version_zero, 47, "North", priority_source.getrandbits(63))
version_two = put(version_one, 61, "East", priority_source.getrandbits(63))
version_three = remove(version_two, 47)
version_four = put(version_two, 83, "West", priority_source.getrandbits(63))
print(ordered(version_one))
print(ordered(version_three))
print(version_four.left is version_two.left)
