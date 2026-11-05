import math


class CaseNode:
    def __init__(self, case_id):
        self.case_id = case_id
        self.left = self.right = None
        self.size = 1


def size(node):
    return node.size if node else 0


class ScapegoatCaseIndex:
    def __init__(self):
        self.root = None
        self.count = 0
        self.rebuilds = 0

    def contains(self, case_id):
        cursor = self.root
        while cursor:
            if case_id == cursor.case_id:
                return True
            cursor = cursor.left if case_id < cursor.case_id else cursor.right
        return False

    def insert(self, case_id):
        if self.root is None:
            self.root = CaseNode(case_id)
            self.count = 1
            return True
        path = []
        cursor = self.root
        while cursor:
            path.append(cursor)
            if case_id == cursor.case_id:
                return False
            next_node = cursor.left if case_id < cursor.case_id else cursor.right
            if next_node is None:
                child = CaseNode(case_id)
                if case_id < cursor.case_id:
                    cursor.left = child
                else:
                    cursor.right = child
                path.append(child)
                break
            cursor = next_node
        self.count += 1
        for ancestor in path[:-1]:
            ancestor.size += 1
        depth_limit = math.floor(math.log(self.count, 1.5))
        if len(path) - 1 <= depth_limit:
            return True
        for position in range(len(path) - 2, -1, -1):
            parent, child = path[position], path[position + 1]
            if 3 * child.size <= 2 * parent.size:
                continue
            nodes = []

            def flatten(node):
                if node is None:
                    return
                flatten(node.left)
                nodes.append(node)
                flatten(node.right)

            def balance(low, high):
                if low >= high:
                    return None
                middle = (low + high) // 2
                node = nodes[middle]
                node.left = balance(low, middle)
                node.right = balance(middle + 1, high)
                node.size = 1 + size(node.left) + size(node.right)
                return node

            flatten(parent)
            rebuilt = balance(0, len(nodes))
            if position == 0:
                self.root = rebuilt
            else:
                grandparent = path[position - 1]
                if grandparent.left is parent:
                    grandparent.left = rebuilt
                else:
                    grandparent.right = rebuilt
            self.rebuilds += 1
            break
        return True

    def ordered_ids(self):
        result = []

        def walk(node):
            if node:
                walk(node.left)
                result.append(node.case_id)
                walk(node.right)

        walk(self.root)
        return result


cases = ScapegoatCaseIndex()
for case_id in [19, 29, 47, 61, 83, 103, 127, 149, 173]:
    cases.insert(case_id)
print(cases.ordered_ids(), cases.rebuilds, cases.contains(83))
