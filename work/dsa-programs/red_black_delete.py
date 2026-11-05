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


def contains(root, deadline):
    current = root
    while current:
        if deadline < current.deadline:
            current = current.left
        elif deadline > current.deadline:
            current = current.right
        else:
            return True
    return False


def prepare_left(parent):
    split_four_node(parent)
    if is_red(parent.right.left):
        parent.right = rotate_right(parent.right)
        parent = rotate_left(parent)
        split_four_node(parent)
    return parent


def prepare_right(parent):
    split_four_node(parent)
    if is_red(parent.left.left):
        parent = rotate_right(parent)
        split_four_node(parent)
    return parent


def repair(parent):
    if is_red(parent.right) and not is_red(parent.left):
        parent = rotate_left(parent)
    if is_red(parent.left) and is_red(parent.left.left):
        parent = rotate_right(parent)
    if is_red(parent.left) and is_red(parent.right):
        split_four_node(parent)
    return parent


def erase_first(parent):
    if parent.left is None:
        return None
    if not is_red(parent.left) and not is_red(parent.left.left):
        parent = prepare_left(parent)
    parent.left = erase_first(parent.left)
    return repair(parent)


def erase_at(parent, deadline):
    if deadline < parent.deadline:
        if not is_red(parent.left) and not is_red(parent.left.left):
            parent = prepare_left(parent)
        parent.left = erase_at(parent.left, deadline)
    else:
        if is_red(parent.left):
            parent = rotate_right(parent)
        if deadline == parent.deadline and parent.right is None:
            return None
        if not is_red(parent.right) and not is_red(parent.right.left):
            parent = prepare_right(parent)
        if deadline == parent.deadline:
            successor = parent.right
            while successor.left:
                successor = successor.left
            parent.deadline = successor.deadline
            parent.right = erase_first(parent.right)
        else:
            parent.right = erase_at(parent.right, deadline)
    return repair(parent)


def remove(root, deadline):
    if not contains(root, deadline):
        return root, False
    if not is_red(root.left) and not is_red(root.right):
        root.red = True
    root = erase_at(root, deadline)
    if root:
        root.red = False
    return root, True


deadline_root = None
for deadline in (47, 52, 61, 19, 26, 58, 83):
    deadline_root = insert(deadline_root, deadline)
for deadline in (26, 47, 83):
    deadline_root, removed = remove(deadline_root, deadline)
    assert removed
print(ordered(deadline_root))
print(audit(deadline_root, float("-inf"), float("inf")) > 0)
