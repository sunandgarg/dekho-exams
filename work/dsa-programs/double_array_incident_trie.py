class IncidentCodeIndex:
    def __init__(self, codes):
        root = {}
        terminals = set()
        for code in codes:
            if not code or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789" for character in code):
                raise ValueError("codes must use lowercase letters or digits")
            node = root
            for character in code:
                node = node.setdefault(character, {})
            terminals.add(code)
        self.base = [0, 0]
        self.check = [-1, -1]
        self.terminal = [False, False]
        pending = [(1, root, "")]
        while pending:
            parent, children, prefix = pending.pop(0)
            self.terminal[parent] = prefix in terminals
            if not children:
                continue
            labels = [(self._label(character), character) for character in children]
            offset = 1
            while any(offset + label < len(self.check) and self.check[offset + label] != -1
                      for label, _ in labels):
                offset += 1
            self.base[parent] = offset
            for label, character in labels:
                slot = offset + label
                while len(self.check) <= slot:
                    self.base.append(0)
                    self.check.append(-1)
                    self.terminal.append(False)
                self.check[slot] = parent
                pending.append((slot, children[character], prefix + character))

    @staticmethod
    def _label(character):
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        return alphabet.index(character) + 1

    def _walk(self, text):
        node = 1
        for character in text:
            if character not in "abcdefghijklmnopqrstuvwxyz0123456789":
                return None
            child = self.base[node] + self._label(character)
            if child >= len(self.check) or self.check[child] != node:
                return None
            node = child
        return node

    def contains(self, code):
        node = self._walk(code)
        return node is not None and self.terminal[node]

    def has_prefix(self, prefix):
        return self._walk(prefix) is not None


if __name__ == "__main__":
    index = IncidentCodeIndex(["dock47", "dock83", "door29", "hub61"])
    print(index.contains("dock47"), index.contains("dock"))
    print(index.has_prefix("dock"), index.has_prefix("dome"))
    print(len(index.base), sum(parent != -1 for parent in index.check))
