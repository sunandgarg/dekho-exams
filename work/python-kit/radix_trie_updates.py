class RadixSet:
    def __init__(self):
        self.root = [False, {}]
        self.size = 0
    def validate(self, key):
        if type(key) is not str or not 1 <= len(key) <= 16 or any(char not in "abcdefghijklmnopqrstuvwxyz" for char in key):
            raise ValueError("bounded ASCII key")
    def contains(self, key):
        self.validate(key)
        node = self.root
        while key:
            edge = next((label for label in node[1] if key.startswith(label)), None)
            if edge is None:
                return False
            key, node = key[len(edge):], node[1][edge]
        return node[0]
    def add(self, key):
        self.validate(key)
        if self.contains(key):
            return False
        if self.size >= 64:
            raise ValueError("key capacity")
        def insert(node, suffix):
            if not suffix:
                node[0] = True
                return
            for label, child in list(node[1].items()):
                shared = 0
                while shared < min(len(label), len(suffix)) and label[shared] == suffix[shared]:
                    shared += 1
                if not shared:
                    continue
                if shared == len(label):
                    insert(child, suffix[shared:])
                else:
                    branch = [False, {label[shared:]: child}]
                    del node[1][label]
                    node[1][label[:shared]] = branch
                    insert(branch, suffix[shared:])
                return
            node[1][suffix] = [True, {}]
        insert(self.root, key)
        self.size += 1
        return True
    def discard(self, key):
        self.validate(key)
        def remove(node, suffix):
            if not suffix:
                if not node[0]:
                    return False
                node[0] = False
                return True
            for label, child in list(node[1].items()):
                if not suffix.startswith(label):
                    continue
                if not remove(child, suffix[len(label):]):
                    return False
                if not child[0] and not child[1]:
                    del node[1][label]
                elif not child[0] and len(child[1]) == 1:
                    extension, descendant = next(iter(child[1].items()))
                    del node[1][label]
                    node[1][label + extension] = descendant
                return True
            return False
        removed = remove(self.root, key)
        self.size -= int(removed)
        return removed

index = RadixSet()
for identifier in ("car", "cart", "carbon", "cat"):
    index.add(identifier)
print("removed prefix:", index.discard("car"))
print("membership:", [index.contains(key) for key in ("car", "cart", "carbon", "cat")])
print("missing removal:", index.discard("cab"))
print("duplicate:", index.add("cart"))
print("size:", index.size)
