class DispatchNode:
    def __init__(self, priority, task_id):
        self.priority, self.task_id = priority, task_id
        self.left = self.right = self
        self.parent = self.child = None
        self.degree = 0
        self.marked = False


def ring_nodes(first):
    if first is None:
        return []
    result, cursor = [], first
    while True:
        result.append(cursor)
        cursor = cursor.right
        if cursor is first:
            return result


def detach(node):
    successor = node.right if node.right is not node else None
    node.left.right = node.right
    node.right.left = node.left
    node.left = node.right = node
    return successor


def insert_before(anchor, node):
    node.left, node.right = anchor.left, anchor
    anchor.left.right = node
    anchor.left = node


class FibonacciDispatchHeap:
    def __init__(self):
        self.minimum = None
        self.handles = {}

    def _add_root(self, node):
        node.parent = None
        node.marked = False
        if self.minimum is None:
            self.minimum = node
        else:
            insert_before(self.minimum, node)
            if (node.priority, node.task_id) < (self.minimum.priority, self.minimum.task_id):
                self.minimum = node

    def insert(self, task_id, priority):
        if task_id in self.handles:
            raise ValueError("duplicate task ID")
        node = DispatchNode(priority, task_id)
        self._add_root(node)
        self.handles[task_id] = node

    def _link(self, child, parent):
        child.parent = parent
        child.marked = False
        if parent.child is None:
            parent.child = child
        else:
            insert_before(parent.child, child)
        parent.degree += 1

    def _consolidate(self):
        roots = ring_nodes(self.minimum)
        for node in roots:
            node.left = node.right = node
        degree_roots = {}
        for node in roots:
            while node.degree in degree_roots:
                other = degree_roots.pop(node.degree)
                if (other.priority, other.task_id) < (node.priority, node.task_id):
                    node, other = other, node
                self._link(other, node)
            degree_roots[node.degree] = node
        self.minimum = None
        for node in degree_roots.values():
            self._add_root(node)

    def pop_minimum(self):
        if self.minimum is None:
            raise IndexError("empty heap")
        removed = self.minimum
        children = ring_nodes(removed.child)
        for child in children:
            child.left = child.right = child
        removed.child = None
        self.minimum = detach(removed)
        for child in children:
            self._add_root(child)
        del self.handles[removed.task_id]
        if self.minimum is not None:
            self._consolidate()
        return removed.priority, removed.task_id

    def _cut(self, node, parent):
        if parent.child is node:
            parent.child = node.right if node.right is not node else None
        detach(node)
        parent.degree -= 1
        self._add_root(node)

    def decrease(self, task_id, new_priority):
        node = self.handles[task_id]
        if new_priority > node.priority:
            raise ValueError("priority cannot increase")
        node.priority = new_priority
        parent = node.parent
        if parent is not None and (node.priority, node.task_id) < (parent.priority, parent.task_id):
            self._cut(node, parent)
            while parent.parent is not None:
                grandparent = parent.parent
                if not parent.marked:
                    parent.marked = True
                    break
                self._cut(parent, grandparent)
                parent = grandparent
        if (node.priority, node.task_id) < (self.minimum.priority, self.minimum.task_id):
            self.minimum = node


if __name__ == "__main__":
    queue = FibonacciDispatchHeap()
    for task_id, priority in [("T-47", 47), ("T-83", 83), ("T-19", 19), ("T-61", 61)]:
        queue.insert(task_id, priority)
    print(queue.pop_minimum())
    queue.decrease("T-83", 17)
    print(queue.pop_minimum())
    print([queue.pop_minimum() for _ in range(2)])
