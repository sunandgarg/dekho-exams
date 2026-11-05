"""Position-indexed treap with lazy range reversal."""

from dataclasses import dataclass
from random import Random


@dataclass
class SequenceNode:
    task_id: str
    priority: float
    left: "SequenceNode | None" = None
    right: "SequenceNode | None" = None
    size: int = 1
    reverse_pending: bool = False


def length(node: SequenceNode | None) -> int:
    return node.size if node else 0


def push(node: SequenceNode | None) -> None:
    if node and node.reverse_pending:
        node.left, node.right = node.right, node.left
        for child in (node.left, node.right):
            if child:
                child.reverse_pending ^= True
        node.reverse_pending = False


def refresh(node: SequenceNode) -> None:
    node.size = 1 + length(node.left) + length(node.right)


def split(node: SequenceNode | None, count: int) -> tuple[SequenceNode | None, SequenceNode | None]:
    if node is None:
        return None, None
    push(node)
    if count <= length(node.left):
        first, node.left = split(node.left, count)
        refresh(node)
        return first, node
    node.right, second = split(node.right, count - length(node.left) - 1)
    refresh(node)
    return node, second


def merge(first: SequenceNode | None, second: SequenceNode | None) -> SequenceNode | None:
    if first is None or second is None:
        return first or second
    if first.priority > second.priority:
        push(first)
        first.right = merge(first.right, second)
        refresh(first)
        return first
    push(second)
    second.left = merge(first, second.left)
    refresh(second)
    return second


class DispatchSequence:
    def __init__(self, seed: int = 47):
        self.root: SequenceNode | None = None
        self.random = Random(seed)

    def insert(self, position: int, task_id: str) -> None:
        if not 0 <= position <= length(self.root):
            raise IndexError(position)
        first, second = split(self.root, position)
        self.root = merge(merge(first, SequenceNode(task_id, self.random.random())), second)

    def reverse(self, start: int, stop: int) -> None:
        if not 0 <= start <= stop <= length(self.root):
            raise IndexError((start, stop))
        first, remainder = split(self.root, start)
        middle, last = split(remainder, stop - start)
        if middle:
            middle.reverse_pending ^= True
        self.root = merge(merge(first, middle), last)

    def snapshot(self) -> list[str]:
        result = []

        def walk(node: SequenceNode | None) -> None:
            if node:
                push(node)
                walk(node.left)
                result.append(node.task_id)
                walk(node.right)

        walk(self.root)
        return result


dispatch = DispatchSequence()
for task_id in ["T-19", "T-47", "T-61", "T-83"]:
    dispatch.insert(length(dispatch.root), task_id)
dispatch.reverse(1, 4)
dispatch.insert(2, "T-26")
print(dispatch.snapshot())
print(length(dispatch.root))
