"""AVL set with subtree sizes for zero-based select and strict rank."""

from dataclasses import dataclass


@dataclass
class OrderNode:
    asset_id: int
    left: "OrderNode | None" = None
    right: "OrderNode | None" = None
    height: int = 1
    size: int = 1


def height(node):
    return node.height if node else 0


def size(node):
    return node.size if node else 0


def refresh(node):
    node.height = 1 + max(height(node.left), height(node.right))
    node.size = 1 + size(node.left) + size(node.right)
    return node


def rotate_left(node):
    replacement = node.right
    node.right = replacement.left
    replacement.left = node
    refresh(node)
    return refresh(replacement)


def rotate_right(node):
    replacement = node.left
    node.left = replacement.right
    replacement.right = node
    refresh(node)
    return refresh(replacement)


def rebalance(node):
    refresh(node)
    difference = height(node.left) - height(node.right)
    if difference > 1:
        if height(node.left.left) < height(node.left.right):
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if difference < -1:
        if height(node.right.right) < height(node.right.left):
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node


def insert(root, asset_id):
    if root is None:
        return OrderNode(asset_id)
    if asset_id == root.asset_id:
        raise ValueError("duplicate asset")
    if asset_id < root.asset_id:
        root.left = insert(root.left, asset_id)
    else:
        root.right = insert(root.right, asset_id)
    return rebalance(root)


def remove_min(root):
    if root.left is None:
        return root.right, root.asset_id
    root.left, minimum = remove_min(root.left)
    return rebalance(root), minimum


def remove(root, asset_id):
    if root is None:
        raise KeyError(asset_id)
    if asset_id < root.asset_id:
        root.left = remove(root.left, asset_id)
    elif asset_id > root.asset_id:
        root.right = remove(root.right, asset_id)
    elif root.left is None:
        return root.right
    elif root.right is None:
        return root.left
    else:
        root.right, root.asset_id = remove_min(root.right)
    return rebalance(root)


def rank(root, asset_id):
    """Number of indexed asset IDs strictly below asset_id."""
    count = 0
    while root:
        if asset_id <= root.asset_id:
            root = root.left
        else:
            count += size(root.left) + 1
            root = root.right
    return count


def select(root, ordinal):
    if ordinal < 0 or ordinal >= size(root):
        raise IndexError("ordinal outside index")
    while root:
        left_count = size(root.left)
        if ordinal < left_count:
            root = root.left
        elif ordinal == left_count:
            return root.asset_id
        else:
            ordinal -= left_count + 1
            root = root.right


asset_root = None
for asset_id in (47, 19, 61, 52, 83):
    asset_root = insert(asset_root, asset_id)
print(select(asset_root, 2), rank(asset_root, 58))
asset_root = remove(asset_root, 47)
print([select(asset_root, ordinal) for ordinal in range(size(asset_root))])
