"""Four traversal contracts for an arbitrary, non-search binary tree."""

from collections import deque
from dataclasses import dataclass


@dataclass
class TaskNode:
    task_id: str
    left: "TaskNode | None" = None
    right: "TaskNode | None" = None


def preorder(root):
    if root is None:
        return []
    pending = [root]
    result = []
    while pending:
        node = pending.pop()
        result.append(node.task_id)
        if node.right is not None:
            pending.append(node.right)
        if node.left is not None:
            pending.append(node.left)
    return result


def inorder(root):
    pending = []
    result = []
    current = root
    while pending or current is not None:
        while current is not None:
            pending.append(current)
            current = current.left
        current = pending.pop()
        result.append(current.task_id)
        current = current.right
    return result


def postorder(root):
    if root is None:
        return []
    pending = [(root, False)]
    result = []
    while pending:
        node, ready = pending.pop()
        if ready:
            result.append(node.task_id)
            continue
        pending.append((node, True))
        if node.right is not None:
            pending.append((node.right, False))
        if node.left is not None:
            pending.append((node.left, False))
    return result


def level_order(root):
    if root is None:
        return []
    pending = deque([root])
    result = []
    while pending:
        node = pending.popleft()
        result.append(node.task_id)
        if node.left is not None:
            pending.append(node.left)
        if node.right is not None:
            pending.append(node.right)
    return result


tasks = TaskNode("T-47", TaskNode("T-19", TaskNode("T-07"), TaskNode("T-26")), TaskNode("T-61"))
print(preorder(tasks))
print(inorder(tasks))
print(postorder(tasks))
print(level_order(tasks))
