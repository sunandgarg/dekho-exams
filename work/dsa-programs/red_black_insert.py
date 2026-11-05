class DeadlineNode:
    def __init__(self, deadline):
        self.deadline = deadline
        self.left = None
        self.right = None
        self.red = True


def is_red(node):
    return node is not None and node.red


def rotate_left(parent):
    promoted = parent.right
    parent.right = promoted.left
    promoted.left = parent
    promoted.red, parent.red = parent.red, True
    return promoted


def rotate_right(parent):
    promoted = parent.left
    parent.left = promoted.right
    promoted.right = parent
    promoted.red, parent.red = parent.red, True
    return promoted


def split_four_node(parent):
    parent.red = not parent.red
    parent.left.red = not parent.left.red
    parent.right.red = not parent.right.red


def insert_at(parent, deadline):
    if parent is None:
        return DeadlineNode(deadline)
    if deadline < parent.deadline:
        parent.left = insert_at(parent.left, deadline)
    elif deadline > parent.deadline:
        parent.right = insert_at(parent.right, deadline)
    else:
        return parent
    if is_red(parent.right) and not is_red(parent.left):
        parent = rotate_left(parent)
    if is_red(parent.left) and is_red(parent.left.left):
        parent = rotate_right(parent)
    if is_red(parent.left) and is_red(parent.right):
        split_four_node(parent)
    return parent


def insert(root, deadline):
    root = insert_at(root, deadline)
    root.red = False
    return root


def ordered(parent):
    if parent is None:
        return []
    return ordered(parent.left) + [parent.deadline] + ordered(parent.right)


def audit(parent, lower, upper):
    if parent is None:
        return 1
    assert lower < parent.deadline < upper
    assert not is_red(parent.right)
    if parent.red:
        assert not is_red(parent.left)
    left_black = audit(parent.left, lower, parent.deadline)
    right_black = audit(parent.right, parent.deadline, upper)
    assert left_black == right_black
    return left_black + (not parent.red)


deadline_root = None
for deadline in (47, 52, 61, 19, 26, 58, 83):
    deadline_root = insert(deadline_root, deadline)
assert not deadline_root.red
print(ordered(deadline_root))
print(audit(deadline_root, float("-inf"), float("inf")) > 0)
