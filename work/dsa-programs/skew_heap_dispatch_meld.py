class DispatchNode:
    def __init__(self, priority, task_id):
        self.priority, self.task_id = priority, task_id
        self.left = None
        self.right = None


def meld_nodes(first, second):
    if first is None:
        return second
    if second is None:
        return first
    if (second.priority, second.task_id) < (first.priority, first.task_id):
        first, second = second, first
    first.right = meld_nodes(first.right, second)
    first.left, first.right = first.right, first.left
    return first


class DispatchSkewHeap:
    def __init__(self):
        self.root = None
        self.size = 0

    def push(self, priority, task_id):
        self.root = meld_nodes(self.root, DispatchNode(priority, task_id))
        self.size += 1

    def merge_from(self, donor):
        if donor is self:
            raise ValueError("cannot meld heap into itself")
        self.root = meld_nodes(self.root, donor.root)
        self.size += donor.size
        donor.root, donor.size = None, 0

    def pop(self):
        if self.root is None:
            raise IndexError("empty heap")
        minimum = self.root
        self.root = meld_nodes(minimum.left, minimum.right)
        self.size -= 1
        return minimum.priority, minimum.task_id


if __name__ == "__main__":
    urgent, routine = DispatchSkewHeap(), DispatchSkewHeap()
    for priority, task in [(47, "T-47"), (19, "T-19")]:
        urgent.push(priority, task)
    for priority, task in [(61, "T-61"), (29, "T-29")]:
        routine.push(priority, task)
    urgent.merge_from(routine)
    print([urgent.pop() for _ in range(4)])
    print(routine.size)
