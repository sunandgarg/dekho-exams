from dataclasses import dataclass

@dataclass
class ReceiptNode:
    key: int
    left: "ReceiptNode | None" = None
    right: "ReceiptNode | None" = None

def receipt_tree(keys):
    if len(keys) > 64 or any(type(key) is not int for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("bounded unique integer keys required")
    def insert(root, key):
        if root is None:
            return ReceiptNode(key)
        if key < root.key:
            root.left = insert(root.left, key)
        else:
            root.right = insert(root.right, key)
        return root
    root = None
    for key in keys:
        root = insert(root, key)
    return root

def delete_receipt(root, key):
    if type(key) is not int:
        raise ValueError("integer key required")
    if root is None:
        return None
    if key < root.key:
        root.left = delete_receipt(root.left, key)
    elif key > root.key:
        root.right = delete_receipt(root.right, key)
    elif root.left is None:
        return root.right
    elif root.right is None:
        return root.left
    else:
        successor = root.right
        while successor.left is not None:
            successor = successor.left
        root.key = successor.key
        root.right = delete_receipt(root.right, successor.key)
    return root

def ordered_receipts(root):
    return [] if root is None else ordered_receipts(root.left) + [root.key] + ordered_receipts(root.right)

root = receipt_tree([41, 20, 60, 50, 70])
root = delete_receipt(root, 41)
print(ordered_receipts(root))
root = delete_receipt(root, 999)
print(ordered_receipts(root))
