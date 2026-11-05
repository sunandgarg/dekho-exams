class WindowNode:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.left = None
        self.right = None
        self.height = 1
        self.max_end = end


def height(node):
    return node.height if node else 0


def refresh(node):
    node.height = 1 + max(height(node.left), height(node.right))
    node.max_end = max(node.end, node.left.max_end if node.left else node.end, node.right.max_end if node.right else node.end)


def rotate_left(old_root):
    new_root = old_root.right
    old_root.right = new_root.left
    new_root.left = old_root
    refresh(old_root)
    refresh(new_root)
    return new_root


def rotate_right(old_root):
    new_root = old_root.left
    old_root.left = new_root.right
    new_root.right = old_root
    refresh(old_root)
    refresh(new_root)
    return new_root


def add_window(node, start, end):
    if start >= end:
        raise ValueError("empty or reversed window")
    if node is None:
        return WindowNode(start, end)
    key = start, end
    current_key = node.start, node.end
    if key < current_key:
        node.left = add_window(node.left, start, end)
    elif key > current_key:
        node.right = add_window(node.right, start, end)
    else:
        return node
    refresh(node)
    difference = height(node.left) - height(node.right)
    if difference > 1:
        if key > (node.left.start, node.left.end):
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if difference < -1:
        if key < (node.right.start, node.right.end):
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node


def first_overlap(node, low, high):
    if low >= high:
        raise ValueError("empty or reversed query")
    while node:
        if node.start < high and low < node.end:
            return node.start, node.end
        if node.left and node.left.max_end > low:
            node = node.left
        else:
            node = node.right
    return None


def remove_window(node, start, end):
    if node is None:
        return None, False
    key = start, end
    current_key = node.start, node.end
    if key < current_key:
        node.left, removed = remove_window(node.left, start, end)
    elif key > current_key:
        node.right, removed = remove_window(node.right, start, end)
    else:
        removed = True
        if node.left is None:
            return node.right, True
        if node.right is None:
            return node.left, True
        successor = node.right
        while successor.left:
            successor = successor.left
        node.start, node.end = successor.start, successor.end
        node.right, _ = remove_window(node.right, successor.start, successor.end)
    if not removed:
        return node, False
    refresh(node)
    difference = height(node.left) - height(node.right)
    if difference > 1:
        if height(node.left.left) < height(node.left.right):
            node.left = rotate_left(node.left)
        node = rotate_right(node)
    elif difference < -1:
        if height(node.right.right) < height(node.right.left):
            node.right = rotate_right(node.right)
        node = rotate_left(node)
    return node, True


window_root = None
for start, end in ((47, 61), (19, 26), (52, 58), (83, 91), (31, 42)):
    window_root = add_window(window_root, start, end)
window_root, removed = remove_window(window_root, 19, 26)
print(removed, first_overlap(window_root, 25, 30))
print(first_overlap(window_root, 62, 80))
print(window_root.height, window_root.max_end)
