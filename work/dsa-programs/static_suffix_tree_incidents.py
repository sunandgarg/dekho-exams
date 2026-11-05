class SuffixNode:
    def __init__(self):
        self.edges = {}
        self.terminal = None


class SuffixEdge:
    def __init__(self, start, end, child):
        self.start, self.end, self.child = start, end, child


class StaticSuffixTree:
    def __init__(self, incident_text, sentinel="$"):
        if sentinel in incident_text or len(sentinel) != 1:
            raise ValueError("sentinel must be unique and one character")
        self.text = incident_text + sentinel
        self.sentinel = sentinel
        self.root = SuffixNode()
        for offset in range(len(self.text)):
            self._insert(offset)

    def _insert(self, offset):
        node, position = self.root, offset
        while position < len(self.text):
            initial = self.text[position]
            edge = node.edges.get(initial)
            if edge is None:
                leaf = SuffixNode()
                leaf.terminal = offset
                node.edges[initial] = SuffixEdge(position, len(self.text), leaf)
                return
            matched = 0
            while (edge.start + matched < edge.end and position + matched < len(self.text)
                   and self.text[edge.start + matched] == self.text[position + matched]):
                matched += 1
            if edge.start + matched == edge.end:
                node, position = edge.child, position + matched
                continue
            branch = SuffixNode()
            node.edges[initial] = SuffixEdge(edge.start, edge.start + matched, branch)
            edge.start += matched
            branch.edges[self.text[edge.start]] = edge
            leaf = SuffixNode()
            leaf.terminal = offset
            branch.edges[self.text[position + matched]] = SuffixEdge(position + matched, len(self.text), leaf)
            return

    def locate(self, pattern):
        if not pattern or self.sentinel in pattern:
            raise ValueError("pattern must be nonempty and omit sentinel")
        node, position = self.root, 0
        while position < len(pattern):
            edge = node.edges.get(pattern[position])
            if edge is None:
                return []
            matched = 0
            while (position + matched < len(pattern) and edge.start + matched < edge.end
                   and pattern[position + matched] == self.text[edge.start + matched]):
                matched += 1
            if position + matched == len(pattern):
                node = edge.child
                break
            if edge.start + matched < edge.end:
                return []
            position += matched
            node = edge.child
        result, pending = [], [node]
        while pending:
            current = pending.pop()
            if current.terminal is not None:
                result.append(current.terminal)
            pending.extend(edge.child for edge in current.edges.values())
        return sorted(result)


if __name__ == "__main__":
    index = StaticSuffixTree("cabacaba")
    print(index.locate("aba"))
    print(index.locate("bac"))
    print(index.locate("zzz"))
