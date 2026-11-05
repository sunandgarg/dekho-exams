class DispatchNode:
    def __init__(self, priority, case_id):
        self.key = (priority, case_id)
        self.left = None
        self.right = None
        self.rank = 1


def null_rank(node):
    return node.rank if node else 0


def meld(first, second):
    if first is None:
        return second
    if second is None:
        return first
    if second.key < first.key:
        first, second = second, first
    first.right = meld(first.right, second)
    if null_rank(first.left) < null_rank(first.right):
        first.left, first.right = first.right, first.left
    first.rank = 1 + null_rank(first.right)
    return first


class LeftistDispatchHeap:
    def __init__(self):
        self.root = None
        self.count = 0

    def push(self, priority, case_id):
        self.root = meld(self.root, DispatchNode(priority, case_id))
        self.count += 1

    def merge_from(self, other):
        if self is other:
            raise ValueError("cannot meld a heap with itself")
        self.root = meld(self.root, other.root)
        self.count += other.count
        other.root, other.count = None, 0

    def pop(self):
        if self.root is None:
            raise IndexError("empty dispatch heap")
        key = self.root.key
        self.root = meld(self.root.left, self.root.right)
        self.count -= 1
        return key


east, west = LeftistDispatchHeap(), LeftistDispatchHeap()
for priority, case_id in [(4, 47), (2, 83), (4, 19)]:
    east.push(priority, case_id)
for priority, case_id in [(1, 61), (3, 29)]:
    west.push(priority, case_id)
east.merge_from(west)
print([east.pop() for _ in range(east.count)], west.count)
