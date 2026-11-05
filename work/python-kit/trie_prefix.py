class LabelTrie:
    def __init__(self):
        self.root = {}
        self.count = 0
    def checked(self, label):
        if type(label) is not str or not 1 <= len(label) <= 32 or any(not "a" <= character <= "z" for character in label):
            raise ValueError("lowercase ASCII label required")
    def insert(self, label):
        self.checked(label)
        if self.contains(label):
            return False
        if self.count == 64:
            raise ValueError("label budget")
        node = self.root
        for character in label:
            node = node.setdefault(character, {})
        node["$"] = True
        self.count += 1
        return True
    def lookup(self, label):
        self.checked(label)
        node = self.root
        for character in label:
            if character not in node:
                return None
            node = node[character]
        return node
    def contains(self, label):
        node = self.lookup(label)
        return node is not None and "$" in node
    def has_prefix(self, label):
        return self.lookup(label) is not None

labels = LabelTrie()
print(labels.insert("ledger"), labels.insert("ledger"))
print(labels.contains("led"), labels.has_prefix("led"))
print(labels.contains("ledger"))
