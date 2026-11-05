class CaseNode:
    def __init__(self, case_id):
        self.case_id = case_id
        self.left = None
        self.right = None
        self.parent = None


class SplayCaseIndex:
    def __init__(self):
        self.root = None

    def _rotate(self, child):
        parent = child.parent
        grandparent = parent.parent
        if child is parent.left:
            parent.left = child.right
            if child.right is not None:
                child.right.parent = parent
            child.right = parent
        else:
            parent.right = child.left
            if child.left is not None:
                child.left.parent = parent
            child.left = parent
        parent.parent = child
        child.parent = grandparent
        if grandparent is None:
            self.root = child
        elif parent is grandparent.left:
            grandparent.left = child
        else:
            grandparent.right = child

    def _splay(self, node):
        while node.parent is not None:
            parent = node.parent
            grandparent = parent.parent
            if grandparent is None:
                self._rotate(node)
            elif (node is parent.left) == (parent is grandparent.left):
                self._rotate(parent)
                self._rotate(node)
            else:
                self._rotate(node)
                self._rotate(node)

    def find(self, case_id):
        current = self.root
        last = None
        while current is not None:
            last = current
            if case_id == current.case_id:
                self._splay(current)
                return True
            current = current.left if case_id < current.case_id else current.right
        if last is not None:
            self._splay(last)
        return False

    def insert(self, case_id):
        if self.root is None:
            self.root = CaseNode(case_id)
            return True
        if self.find(case_id):
            return False
        old_root = self.root
        fresh = CaseNode(case_id)
        if case_id < old_root.case_id:
            fresh.left = old_root.left
            if fresh.left is not None:
                fresh.left.parent = fresh
            fresh.right = old_root
            old_root.left = None
        else:
            fresh.right = old_root.right
            if fresh.right is not None:
                fresh.right.parent = fresh
            fresh.left = old_root
            old_root.right = None
        old_root.parent = fresh
        self.root = fresh
        return True

    def remove(self, case_id):
        if not self.find(case_id):
            return False
        old_root = self.root
        left, right = old_root.left, old_root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None
        old_root.left = old_root.right = None
        if left is None:
            self.root = right
            return True
        self.root = left
        maximum = left
        while maximum.right is not None:
            maximum = maximum.right
        self._splay(maximum)
        self.root.right = right
        if right is not None:
            right.parent = self.root
        return True

    def ordered_ids(self):
        result = []
        stack = []
        current = self.root
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            result.append(current.case_id)
            current = current.right
        return result


cases = SplayCaseIndex()
for case_id in (47, 19, 83, 61):
    cases.insert(case_id)
print(cases.ordered_ids())
print(cases.find(19), cases.root.case_id)
print(cases.find(55), cases.root.case_id)
print(cases.remove(47), cases.ordered_ids())
