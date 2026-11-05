from dataclasses import dataclass

@dataclass
class IndexNode:
    key: int
    left: "IndexNode | None" = None
    right: "IndexNode | None" = None
    height: int = 1

def height(node):
    return node.height if node else 0

def refresh(node):
    node.height = 1 + max(height(node.left), height(node.right))

def rotate_right(node):
    replacement = node.left
    node.left = replacement.right
    replacement.right = node
    refresh(node); refresh(replacement)
    return replacement

def rotate_left(node):
    replacement = node.right
    node.right = replacement.left
    replacement.left = node
    refresh(node); refresh(replacement)
    return replacement

def insert_key(node, key):
    if node is None:
        return IndexNode(key)
    if key < node.key:
        node.left = insert_key(node.left, key)
    elif key > node.key:
        node.right = insert_key(node.right, key)
    else:
        return node
    refresh(node)
    balance = height(node.left) - height(node.right)
    if balance > 1:
        if key > node.left.key:
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if balance < -1:
        if key < node.right.key:
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node

class ReceiptIndex:
    def __init__(self):
        self.root = None
        self.keys = set()
    def add(self, key):
        if type(key) is not int or (key not in self.keys and len(self.keys) >= 128):
            raise ValueError("index key budget rejected")
        self.root = insert_key(self.root, key)
        self.keys.add(key)

index = ReceiptIndex()
for key in (10, 20, 30, 40, 50):
    index.add(key)
print("root:", index.root.key)
print("height:", index.root.height)
index.add(30)
print("unique keys:", len(index.keys))
