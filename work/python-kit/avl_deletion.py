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

def delete_key(node, key):
    if node is None:
        return None
    if key < node.key:
        node.left = delete_key(node.left, key)
    elif key > node.key:
        node.right = delete_key(node.right, key)
    else:
        if node.left is None: return node.right
        if node.right is None: return node.left
        successor = node.right
        while successor.left is not None: successor = successor.left
        node.key = successor.key
        node.right = delete_key(node.right, successor.key)
    refresh(node)
    balance = height(node.left) - height(node.right)
    if balance > 1:
        if height(node.left.left) < height(node.left.right):
            node.left = rotate_left(node.left)
        return rotate_right(node)
    if balance < -1:
        if height(node.right.right) < height(node.right.left):
            node.right = rotate_right(node.right)
        return rotate_left(node)
    return node

class RemovableIndex(ReceiptIndex):
    def remove(self, key):
        if type(key) is not int:
            raise ValueError("exact integer key required")
        if key not in self.keys:
            return False
        self.root = delete_key(self.root, key)
        self.keys.remove(key)
        return True

index = RemovableIndex()
for key in (10, 20, 30, 40, 50, 25): index.add(key)
print(index.remove(30), sorted(index.keys))
print(index.remove(30), sorted(index.keys))
for key in tuple(index.keys): index.remove(key)
print("empty root:", index.root is None)
