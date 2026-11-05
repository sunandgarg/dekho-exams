class AlertTrieNode:
    def __init__(self):
        self.children = {}
        self.terminal = False


class LevelOrderAlertTrie:
    def __init__(self, terms):
        root = AlertTrieNode()
        for term in terms:
            node = root
            for character in term:
                node = node.children.setdefault(character, AlertTrieNode())
            node.terminal = True
        self.degree_bits = []
        self.edge_labels = []
        self.terminal = []
        self.zero_positions = []
        self.rank_ones = []
        queue = [root]
        cursor = 0
        ones = 0
        while cursor < len(queue):
            node = queue[cursor]
            cursor += 1
            self.terminal.append(node.terminal)
            for label, child in sorted(node.children.items()):
                self.degree_bits.append(1)
                ones += 1
                self.rank_ones.append(ones)
                self.edge_labels.append(label)
                queue.append(child)
            self.degree_bits.append(0)
            self.rank_ones.append(ones)
            self.zero_positions.append(len(self.degree_bits) - 1)

    def _follow(self, prefix):
        node_id = 0
        for character in prefix:
            start = self.zero_positions[node_id - 1] + 1 if node_id else 0
            end = self.zero_positions[node_id]
            child_id = None
            for position in range(start, end):
                candidate = self.rank_ones[position]
                label = self.edge_labels[candidate - 1]
                if label == character:
                    child_id = candidate
                    break
                if label > character:
                    break
            if child_id is None:
                return None
            node_id = child_id
        return node_id

    def contains(self, term):
        node_id = self._follow(term)
        return node_id is not None and self.terminal[node_id]

    def has_prefix(self, prefix):
        return self._follow(prefix) is not None


terms = LevelOrderAlertTrie(["alert", "alloy", "bay", "badge"])
print("alert=", terms.contains("alert"), " al-prefix=", terms.has_prefix("al"),
      " al-key=", terms.contains("al"), " nodes=", len(terms.terminal), sep="")
