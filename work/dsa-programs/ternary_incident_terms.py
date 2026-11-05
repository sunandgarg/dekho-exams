class TermNode:
    def __init__(self, character):
        self.character = character
        self.left = None
        self.equal = None
        self.right = None
        self.terminal = False


class IncidentTermIndex:
    def __init__(self):
        self.root = None
        self.empty_term = False

    def insert(self, term):
        if not isinstance(term, str):
            raise TypeError("term must be text")
        if not term:
            self.empty_term = True
            return

        def place(node, offset):
            character = term[offset]
            if node is None:
                node = TermNode(character)
            if character < node.character:
                node.left = place(node.left, offset)
            elif character > node.character:
                node.right = place(node.right, offset)
            elif offset + 1 == len(term):
                node.terminal = True
            else:
                node.equal = place(node.equal, offset + 1)
            return node

        self.root = place(self.root, 0)

    def _terminal_node(self, term):
        node = self.root
        offset = 0
        while node is not None:
            character = term[offset]
            if character < node.character:
                node = node.left
            elif character > node.character:
                node = node.right
            elif offset + 1 == len(term):
                return node
            else:
                offset += 1
                node = node.equal
        return None

    def contains(self, term):
        if not term:
            return self.empty_term
        node = self._terminal_node(term)
        return node is not None and node.terminal

    def complete(self, prefix):
        if not prefix:
            base = self.root
            results = [""] if self.empty_term else []
        else:
            terminal = self._terminal_node(prefix)
            if terminal is None:
                return []
            results = [prefix] if terminal.terminal else []
            base = terminal.equal

        def collect(node, stem):
            if node is None:
                return
            collect(node.left, stem)
            word = stem + node.character
            if node.terminal:
                results.append(word)
            collect(node.equal, word)
            collect(node.right, stem)

        collect(base, prefix)
        return results


terms = IncidentTermIndex()
for label in ("alarm", "alert", "alpine", "valve", "al"):
    terms.insert(label)
print("al=", terms.complete("al"), " exact=", terms.contains("alp"), sep="")
