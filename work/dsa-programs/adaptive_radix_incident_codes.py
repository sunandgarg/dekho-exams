class RadixNode:
    def __init__(self, prefix=b"", value=None):
        self.prefix = prefix
        self.value = value
        self.tier = 4
        self.labels = []
        self.children = []
        self.index = None
        self.count = 0

    def items(self):
        if self.tier <= 16:
            return list(zip(self.labels, self.children))
        if self.tier == 48:
            return [(label, self.children[position]) for label, position in enumerate(self.index)
                    if position != -1]
        return [(label, child) for label, child in enumerate(self.children) if child is not None]

    def get(self, label):
        if self.tier <= 16:
            return self.children[self.labels.index(label)] if label in self.labels else None
        if self.tier == 48:
            position = self.index[label]
            return None if position == -1 else self.children[position]
        return self.children[label]

    def put(self, label, child):
        if self.get(label) is not None:
            if self.tier <= 16:
                self.children[self.labels.index(label)] = child
            elif self.tier == 48:
                self.children[self.index[label]] = child
            else:
                self.children[label] = child
            return
        if self.count == self.tier and self.tier < 256:
            old = self.items()
            self.tier = {4: 16, 16: 48, 48: 256}[self.tier]
            self.labels = []
            self.children = [] if self.tier < 256 else [None] * 256
            self.index = [-1] * 256 if self.tier == 48 else None
            self.count = 0
            for old_label, old_child in old:
                self.put(old_label, old_child)
        if self.tier <= 16:
            self.labels.append(label)
            self.children.append(child)
        elif self.tier == 48:
            self.index[label] = len(self.children)
            self.children.append(child)
        else:
            self.children[label] = child
        self.count += 1


class AdaptiveIncidentCodes:
    def __init__(self):
        self.root = RadixNode()

    def insert(self, code, incident_id):
        if not isinstance(code, bytes):
            raise TypeError("incident code must be bytes")

        def place(node, suffix):
            common = 0
            while common < min(len(node.prefix), len(suffix)) and node.prefix[common] == suffix[common]:
                common += 1
            if common < len(node.prefix):
                parent = RadixNode(node.prefix[:common])
                old_label = node.prefix[common]
                node.prefix = node.prefix[common + 1:]
                parent.put(old_label, node)
                if common == len(suffix):
                    parent.value = incident_id
                else:
                    parent.put(suffix[common], RadixNode(suffix[common + 1:], incident_id))
                return parent
            suffix = suffix[common:]
            if not suffix:
                node.value = incident_id
            else:
                label = suffix[0]
                child = node.get(label)
                node.put(label, RadixNode(suffix[1:], incident_id) if child is None
                         else place(child, suffix[1:]))
            return node

        self.root = place(self.root, code)

    def lookup(self, code):
        if not isinstance(code, bytes):
            raise TypeError("incident code must be bytes")
        node, suffix = self.root, code
        while node is not None:
            if not suffix.startswith(node.prefix):
                return None
            suffix = suffix[len(node.prefix):]
            if not suffix:
                return node.value
            node = node.get(suffix[0])
            suffix = suffix[1:]
        return None


if __name__ == "__main__":
    index = AdaptiveIncidentCodes()
    for number in range(19):
        index.insert(b"rack" + bytes([number]), 4700 + number)
    index.insert(b"rack", 83)
    print(index.lookup(b"rack"), index.lookup(b"rack\x12"), index.lookup(b"rack\x13"))
    rack_node = index.root.get(ord("r"))
    print(rack_node.prefix, rack_node.tier, rack_node.count)
